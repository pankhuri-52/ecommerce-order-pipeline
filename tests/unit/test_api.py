import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(monkeypatch):
    # Mock Redis BEFORE importing app
    class FakeRedis:
        def hgetall(self, key):
            return {"total_orders": "5", "total_revenue": "500.0"}

    import web.main as main
    main.redis_client = FakeRedis()

    return TestClient(main.app)

def test_get_global_stats(client):
    response = client.get("/stats/global")
    assert response.status_code == 200
    assert response.json() == {"total_orders": 5, "total_revenue": 500.0}
