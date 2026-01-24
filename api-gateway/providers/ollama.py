import os
import time
import uuid
import httpx


from models import ChatRequest, ChatResponse, ChatMessage, ChatChoice, Usage
from providers.base import LLMProvider

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_URL = f"http://{OLLAMA_HOST}:11434"


class OllamaProvider(LLMProvider):
   """Local Ollama instance - private, no API costs"""

   name = "ollama"

   def __init__(self, redis_client=None, model_prefixes: list[str] = None, base_url: str = None):
      # Use environment variable or default
      super().__init__(redis_client, model_prefixes)
      self.base_url = base_url or OLLAMA_URL

   def is_available(self) -> bool:
      """Verify Ollama is reachable"""
      try:
         response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
         return response.status_code == 200
      except Exception:
         return False
   
   async def chat(self, request: ChatRequest) -> ChatResponse:
      """Convert OpenAI format to Ollama format and call"""
      # Ollama uses a sinlge prompt string, not messages array - combinr into a prompt
      prompt = self._messages_to_prompt(request.messages)

      async with httpx.AsyncClient(timeout=60.0) as client:
         response = await client.post(
            f"{self.base_url}/api/generate",
            json={
               "model": request.model,
               "prompt": prompt,
               "stream": False,
               "options": {
                  "temperature": request.temperature,
                  "num_predict": request.max_tokens
               }
            }
         )
         data = response.json()

      # Build standardized response
      result = ChatResponse(
         id=f"ollama-{uuid.uuid4().hex[:8]}",
         object="chat.completion",
         created=int(time.time()),
         model=request.model,
         provider=self.name,
         choices=[
            ChatChoice(
               index=0,
               message=ChatMessage(role="assistant", content=data.get("response", "")),
               finish_reason="stop" if data.get("done") else "length"
            )
         ],
         usage=Usage(
            prompt_tokens=data.get("prompt_eval_count") or 0,
            completion_tokens=data.get("eval_count") or 0,
            total_tokens=(data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0)
         )
      )

      # Log to redis
      self.log_usage(result)

      return result
   
   def _messages_to_prompt(self, messages: list[ChatMessage]) -> str:
      """Convert OpenAI style messages to a single prompt string"""
      prompt_parts = []
      for msg in messages:
         if msg.role == "system":
            prompt_parts.append(f"System: {msg.content}")
         elif msg.role == "user":
            prompt_parts.append(f"User: {msg.content}")
         elif msg.role == "assistant":
            prompt_parts.append(f"Assistant: {msg.content}")

      prompt_parts.append("Assistant:") # Prompt for response
      return "\n\n".join(prompt_parts)