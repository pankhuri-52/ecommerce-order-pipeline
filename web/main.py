from fastapi import FastAPI, HTTPException, Request
import redis
import time
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(
    title="E-Commerce Order Pipeline API",
    description="API for retrieving order statistics and aggregates",
    version="1.0.0"
)

# Redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"➤ {request.method} {request.url.path} - Client: {request.client.host}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    status_emoji = "✅" if response.status_code < 400 else "❌"
    logger.info(
        f"{status_emoji} {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring service availability"""
    try:
        # Test Redis connection
        ping_time = time.time()
        redis_client.ping()
        redis_latency = round((time.time() - ping_time) * 1000, 2)
        
        return {
            "status": "healthy", 
            "redis": "connected",
            "redis_latency_ms": redis_latency,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Unhealthy: {str(e)}")

@app.get("/metrics")
def get_metrics():
    """Metrics endpoint for monitoring system performance"""
    try:
        # Basic metrics for monitoring
        global_stats = redis_client.hgetall("global:stats")
        users_count = redis_client.zcard("users:by_spend")
        
        return {
            "total_orders": int(global_stats.get("total_orders", 0)),
            "total_revenue": float(global_stats.get("total_revenue", 0.0)),
            "unique_users": users_count,
            "average_order_value": (
                float(global_stats.get("total_revenue", 0.0)) / 
                max(int(global_stats.get("total_orders", 1)), 1)
            ),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Metrics unavailable: {str(e)}")

@app.get("/users/{user_id}/stats")
def get_user_stats(user_id: str):
    stats = redis_client.hgetall(f"user:{user_id}") 
    if not stats:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user_id,
        "order_count": int(stats.get("order_count", 0)),
        "total_spend": float(stats.get("total_spend", 0.0))
    }

@app.get("/stats/global")
def get_global_stats():
    stats = redis_client.hgetall("global:stats")
    return {
        "total_orders": int(stats.get("total_orders", 0)),
        "total_revenue": float(stats.get("total_revenue", 0.0))
    }

@app.get("/stats/top-spenders")
def top_spenders(limit: int = 5):
    top_users = redis_client.zrevrange("users:by_spend", 0, limit-1, withscores=True)
    return [{"user_id": user, "total_spend": spend} for user, spend in top_users]

@app.get("/stats/top-buyers")
def top_buyers(limit: int = 5):
    top_users = redis_client.zrevrange("users:by_count", 0, limit-1, withscores=True)
    return [{"user_id": user, "order_count": int(count)} for user, count in top_users]

@app.get("/stats/by-date")
def stats_by_date(start_date: str, end_date: str):
    from datetime import datetime, timedelta
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    total_orders = 0
    total_revenue = 0.0

    current = start
    while current <= end:
        date_key = f"stats:{current.strftime('%Y-%m-%d')}"
        stats = redis_client.hgetall(date_key)
        total_orders += int(stats.get("orders", 0))
        total_revenue += float(stats.get("revenue", 0.0))
        current += timedelta(days=1)

    return {"total_orders": total_orders, "total_revenue": total_revenue}

