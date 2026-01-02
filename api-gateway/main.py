import os
from fastapi import FastAPI
import redis

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

