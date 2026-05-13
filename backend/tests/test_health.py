"""GET /health endpoint."""
from unittest.mock import patch

from sqlalchemy.exc import OperationalError


def test_health_returns_200_when_db_is_up(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["version"]


def test_health_returns_503_when_db_query_fails(client):
    with patch("testjam.routers.health.text") as fake_text:
        fake_text.side_effect = OperationalError("SELECT 1", {}, Exception("boom"))

        response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["db"] == "down"


def test_health_does_not_require_authentication(client):
    response = client.get("/health")

    assert response.status_code == 200
