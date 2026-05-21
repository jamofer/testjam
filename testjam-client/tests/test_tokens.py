"""API token SDK coverage (user + project scopes)."""


def test_create_user_token_returns_raw_value(auth_client):
    created = auth_client.tokens.create_user_token("ci")

    assert created["name"] == "ci"
    assert created["token"].startswith(created["prefix"])
    assert created["user_id"] is not None
    assert created["project_id"] is None


def test_list_user_tokens(auth_client):
    auth_client.tokens.create_user_token("one")
    auth_client.tokens.create_user_token("two")

    listing = auth_client.tokens.list_user_tokens()

    assert {t["name"] for t in listing} == {"one", "two"}
    assert all("token" not in t for t in listing)


def test_rotate_user_token_returns_new_value(auth_client):
    created = auth_client.tokens.create_user_token("rot")

    rotated = auth_client.tokens.rotate_user_token(created["id"])

    assert rotated["id"] == created["id"]
    assert rotated["token"] != created["token"]


def test_delete_user_token(auth_client):
    created = auth_client.tokens.create_user_token("gone")

    auth_client.tokens.delete_user_token(created["id"])

    assert auth_client.tokens.list_user_tokens() == []


def test_project_token_lifecycle(auth_client):
    project = auth_client.projects.find_or_create("TokenProj")

    created = auth_client.tokens.create_project_token(project["id"], "robot")
    listing = auth_client.tokens.list_project_tokens(project["id"])
    rotated = auth_client.tokens.rotate_project_token(project["id"], created["id"])

    assert created["project_id"] == project["id"]
    assert [t["id"] for t in listing] == [created["id"]]
    assert rotated["token"] != created["token"]

    auth_client.tokens.delete_project_token(project["id"], created["id"])
    assert auth_client.tokens.list_project_tokens(project["id"]) == []
