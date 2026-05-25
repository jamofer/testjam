"""GET /api/v1/about endpoint."""


def test_about_returns_env_injected_metadata(client, monkeypatch):
    monkeypatch.setenv("TESTJAM_VERSION_REF", "v1.0.0")
    monkeypatch.setenv("TESTJAM_VERSION_COMMIT", "abc1234")
    monkeypatch.setenv("TESTJAM_BUILD_DATE", "2026-05-25T12:00:00Z")

    response = client.get("/api/v1/about")

    assert response.status_code == 200
    body = response.json()
    assert body["version"]
    assert body["ref"] == "v1.0.0"
    assert body["commit"] == "abc1234"
    assert body["built_at"] == "2026-05-25T12:00:00Z"


def test_about_falls_back_to_unknown_when_env_unset(client, monkeypatch):
    monkeypatch.delenv("TESTJAM_VERSION_REF", raising=False)
    monkeypatch.delenv("TESTJAM_VERSION_COMMIT", raising=False)
    monkeypatch.delenv("TESTJAM_BUILD_DATE", raising=False)

    response = client.get("/api/v1/about")

    assert response.status_code == 200
    body = response.json()
    assert body["ref"] == "unknown"
    assert body["commit"] == "unknown"
    assert body["built_at"] == "unknown"


def test_about_does_not_require_authentication(client):
    response = client.get("/api/v1/about")

    assert response.status_code == 200
