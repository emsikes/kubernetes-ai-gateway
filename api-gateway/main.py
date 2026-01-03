import os
from fastapi import FastAPI
import redis
import json
import httpx


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_URL = f"http://{OLLAMA_HOST}:11434"

app = FastAPI(title="AI Gateway")

# Connect to Redis using environment variables (with fallback for local dev)
redis_host = os.getenv("APP_REDIS_HOST", "localhost")
redis_port = "6379"
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

@app.get("/health")
def health_check():
   return {"status": "healthy"}

@app.get("/redis-test")
def redis_test():
   # Send and get value to confirm connectivity
   redis_client.set("test_key", "hello from k8s")
   value = redis_client.get("test_key")
   return {"redis_value": value}   

@app.get("/config")
def get_config():
   return {
      "app_name": os.getenv("APP_NAME", "Unkown"),
      "log_level": os.getenv("LOG_LEVEL", "INFO"),
      "rate_limit_per_minute": os.getenv("RATE_LIMIT_PER_MINUTE", "60")
    } 

@app.get("/providers")
def list_providers():
   """Show which LLM providers and configured"""
   providers = {}

   openai_key = os.getenv("OPENAI_API_KEY", "")
   anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

   providers["openai"] = {
      "configured": len(openai_key) > 0,
      "key_preview": f"{openai_key[:7]}..." if len(openai_key) > 7 else "not set"
   }
   providers["anthropic"] = {
      "configured": len(anthropic_key) > 0,
      "key_preview": f"{anthropic_key[:7]}..." if len(anthropic_key) > 7 else "not set"
   }
   providers["ollama"] = {
      "configured": True,
      "key_preview": "no key required (local)"
   }

   return providers

@app.get("/settings")
def get_settings():
   try:
      with open("/app/config/settings.json", "r") as f:
         settings = json.load(f)
      return settings
   except FileNotFoundError:
      return {"error": "Settings file not found"}
   
@app.post("/chat")
async def chat(request: dict):
   """Forward chat request to Ollama"""
   async with httpx.AsyncClient(timeout=60.0) as client:
      response = await client.post(
         f"{OLLAMA_URL}/api/generate",
         json={
            "model": request.get("model", "llama3.2:1b"),
            "prompt": request.get("prompt", ""),
            "stream": False
         }
      )
      return response.json()