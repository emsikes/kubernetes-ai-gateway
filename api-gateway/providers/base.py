from abc import ABC, abstractmethod
import time
import os

from models import ChatRequest, ChatResponse


class LLMProvider(ABC):
   """Base class all providers must implement"""

   name: str # "ollama", "openai", "anthropic", "bedrock"

   def __init__(self, redis_client=None, model_prefixes: list[str] = None):
      """Initialize the optional Redis client for usage tracking"""
      self._redis = redis_client
      self._model_prefixes = model_prefixes or []

   @abstractmethod
   async def chat(self, request: ChatRequest) -> ChatResponse:
      """Send chat request, return standardized response"""
      pass

   @abstractmethod
   def is_available(self) -> bool:
      """Check if provider is configured and reachable"""
      pass

   def supports_model(self, model: str) -> bool:
      """Check if this provider handles the requested model"""
      if not self._model_prefixes:
        return False
      
      model_lower = model.lower()

      # Special case: Ollama models often have a ":" (e.g. llama3.2:1b)
      if ":" in model:
         return True
   
   def log_usage(self, response: ChatResponse):
      """Track tokens and requests in Redis"""
      if not self._redis:
         return
    
      today = time.strftime('%Y-%m-%d')
      key = f"usage:{self.name}:{today}"

      if response.usage:
         self._redis.hincrby(key, "prompt_tokens", response.usage.prompt_tokens)
         self._redis.hincrby(key, "completion_tokens", response.usage.completion_tokens)

      self._redis.hincrby(key, "requests", 1)
      self._redis.expire(key, 86400 * 30) # Keep 30 days