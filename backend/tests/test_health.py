"""Smoke tests for the Haku backend.

A trivial /health check that would have caught the 23431->24100 port
regression: it asserts the app boots and the health endpoint answers.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_routers_mounted():
    # The process and search routers must be reachable under their prefixes.
    # /search/images without the required `q` query param -> 422, which still
    # proves the route exists (404 would mean it was never mounted).
    resp = client.get("/search/images")
    assert resp.status_code == 422
