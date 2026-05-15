"""User-level date/timezone preferences."""


def test_default_user_has_no_timezone_and_relative_dates_on(auth_client):
    me = auth_client.get("/api/v1/users/me").json()

    assert me["timezone"] is None
    assert me["use_relative_dates"] is True


def test_update_timezone_persists(auth_client):
    auth_client.put("/api/v1/users/me", json={"timezone": "Europe/Madrid"})

    me = auth_client.get("/api/v1/users/me").json()
    assert me["timezone"] == "Europe/Madrid"


def test_timezone_must_be_iana(auth_client):
    resp = auth_client.put("/api/v1/users/me", json={"timezone": "Mars/Olympus"})

    assert resp.status_code == 422


def test_toggle_relative_dates_off(auth_client):
    auth_client.put("/api/v1/users/me", json={"use_relative_dates": False})

    me = auth_client.get("/api/v1/users/me").json()
    assert me["use_relative_dates"] is False
