from fastapi.testclient import TestClient
from ai_backend.app.main import app


def test_health_endpoint():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
