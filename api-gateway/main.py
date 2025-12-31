import os
from fastapi import FastAPI
import redis

app = FastAPI(title="AI Gateway")

redis_host = os.getenv("APP_REDIS_HOST", "redis")
redis_port = int(os.getenv("APP_REDIS_PORT", "6379"))

# Initialize Redis client connection
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

@app.get("/health")
def health_check():
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.ConnectionError:
        return {"status": "degraded", "redis": "disconnected"}
