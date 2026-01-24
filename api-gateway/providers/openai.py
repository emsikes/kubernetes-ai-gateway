import os
import time
import uuid
import httpx

from models import ChatRequest, ChatResponse, ChatMessage, ChatChoice, Usage
from providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI API - GPT models"""

    name = "openai"

    def __init__(self, redis_client=None, model_prefixes: list[str] = None):
        super().__init__(redis_client, model_prefixes)
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = "https://api.openai.com/v1"

    def is_available(self) -> bool:
        """Check if API key is configured - no API ping to OpenAI which would incur costs"""
        return len(self.api_key) > 0

    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Call OpenAI"""

        # Convert Pydantic models to dicts for the API
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        # Create HTTP connection and auto-close when done
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": request.model,
                    "messages": messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            data = response.json()

        """Handle API errors for:
            - Invalid API Key
            - Rate limits
            - Model not found
            - Quota exceeded
        """
        if "error" in data:
            return ChatResponse(
                id=f"openai-error-{uuid.uuid4().hex[:8]}",
                object="chat.completion",
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=f"Error: {data['error']['message']}"),
                        finish_reason="error"
                    )
                ],
                usage=None
            )
        
        # Map OpenAI response format to ours
        choice = data["choices"][0]
        result = ChatResponse(
            id=data.get("id", f"openai-{uuid.uuid4().hex[:8]}"),
            object="chat.completion",
            created=data.get("created", int(time.time())),
            model=data.get("model", request.model),
            provider=self.name,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(
                        role=choice["message"]["role"],
                        content=choice["message"]["content"]
                    ),
                   finish_reason=choice.get("finish_reason", "stop")
               )
            ],
            usage=Usage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"]
            ) if "usage" in data else None
        )

        self.log_usage(result)
        return result