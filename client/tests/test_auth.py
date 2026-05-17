import pytest

from testjam_client import Unauthorized


def test_login_returns_token(seeded_user, client):
    token = client.login("alice", "pw")

    assert isinstance(token, str)
    assert token
    me = client.request("GET", "/users/me").json()
    assert me["username"] == "alice"


def test_login_wrong_password_raises_unauthorized(seeded_user, client):
    with pytest.raises(Unauthorized):
        client.login("alice", "wrong")
