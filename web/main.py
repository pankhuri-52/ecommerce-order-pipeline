from fastapi import FastAPI, HTTPException
import redis

app = FastAPI()

# Redis connection
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

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

