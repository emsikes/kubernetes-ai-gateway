"""
Content Safety Guardrail
Evaluates prompts for harmful content based on configurable categories
"""
import json
import logging
from typing import Dict, List

from models import ChatRequest
from .base import (
    GuardrailBase,
    GuardrailResult,
    ThreatCategory,
    Severity,
    GuardrailAction
)

logger = logging.getLogger(__name__)


class ContentSafetyGuard(GuardrailBase):
    """
    Keyword based content safety evaluation
    Loads categories and keywords from guardrail-settings ConfigMap
    """

    def __init__(self, config: dict):
        """
        Initialize with config from content_safety.json 
        
        Args:
            config: Parsed JSON from ConfigMap
        """
        super().__init__(config)
        self.categories = config.get("categories", {})
        self.default_action = config.get("default_action", "block")
        self.log_all = config.get("log_all_requests", False)

    def name(self) -> str:
        """Return guardrail identifier for logging"""
        return "content_safety"
    
    def evaluate(self, request: ChatRequest) -> GuardrailResult:
        """
        Evaluate a chat request for harmful content

        Args:
            request: Incoming ChatRequest with messages

        Returns:
            GuardrailResult indicating pass/fail and details
        """
        # Skip if guardrail is disabled
        if not self.is_enabled():
            return GuardrailResult(passed=True)
        
        # Extract all text from the request message
        text_to_check = self._extract_text(request)

        # Check against each enabled category
        for category_name, category_config in self.categories.items():
            if not category_config.get("enabled", True):
                continue

            result = self._check_category(text_to_check, category_name, category_config)
            if not result.passed:
                logger.warning(f"Content flagged: category={category_name}, confidence={result.confidence}")
                return result
            
        # All checks passed
        if self.log_all:
            logger.info(f"Request passed content safety: {text_to_check[:100]}...")

        return GuardrailResult(passed=True)
    
    def _extract_text(self, request: ChatRequest) -> str:
        """
        Combine all message content into a single string for checking

        Args:
            request: ChatRequest containing messages

        Returns:
            Lowercase concatenated text from all messages
        """
        texts = []
        for message in request.messages:
            if message.content:
                texts.append(message.content)

        return " ".join(texts).lower()