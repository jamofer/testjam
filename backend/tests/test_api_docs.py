"""API docs must load through the reverse proxy, which only forwards /api/."""

PROXIED_PREFIX = "/api/"


def test_openapi_schema_is_served_under_the_api_prefix(client):
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    assert response.json()["openapi"].startswith("3.")


def test_swagger_ui_loads_the_schema_from_the_api_prefix(client):
    page = client.get("/api/docs").text

    assert f"url: '{PROXIED_PREFIX}openapi.json'" in page


def test_redoc_loads_the_schema_from_the_api_prefix(client):
    page = client.get("/api/redoc").text

    assert f'spec-url="{PROXIED_PREFIX}openapi.json"' in page
