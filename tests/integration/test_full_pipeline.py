import pytest
import boto3
from fastapi.testclient import TestClient
import time
import os
import json

os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def client(monkeypatch):
    # Mock Redis for integration tests
    class MockRedis:
        def __init__(self):
            self.data = {}
            
        def hgetall(self, key):
            return self.data.get(key, {})
            
        def hincrby(self, key, field, amount):
            if key not in self.data:
                self.data[key] = {}
            self.data[key][field] = str(int(self.data[key].get(field, 0)) + amount)
            
        def hincrbyfloat(self, key, field, amount):
            if key not in self.data:
                self.data[key] = {}
            self.data[key][field] = str(float(self.data[key].get(field, 0.0)) + amount)
            
        def zincrby(self, key, amount, member):
            # Simple mock for sorted sets
            pass
            
        def zrevrange(self, key, start, end, withscores=False):
            return []

    # Import and patch AFTER setting up mock
    import web.main as main
    mock_redis = MockRedis()
    main.redis_client = mock_redis
    
    return TestClient(main.app), mock_redis

@pytest.mark.integration
def test_full_pipeline(client):
    test_client, mock_redis = client
    
    # Simulate worker processing by directly updating Redis
    mock_redis.hincrby("global:stats", "total_orders", 1)
    mock_redis.hincrbyfloat("global:stats", "total_revenue", 50.0)
    
    # Check stats via API
    response = test_client.get("/stats/global")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_orders"] == 1
    assert stats["total_revenue"] == 50.0
