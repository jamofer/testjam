"""Outbound webhook SDK coverage."""


def _seed_webhook(auth_client):
    project = auth_client.projects.find_or_create("HookProj")
    hook = auth_client.webhooks.create(
        project["id"],
        name="ci",
        url="https://example.com/hook",
        events=["execution.completed", "bug.created"],
    )
    return project, hook


def test_create_returns_secret(auth_client):
    _, hook = _seed_webhook(auth_client)

    assert hook["name"] == "ci"
    assert hook["events"] == ["execution.completed", "bug.created"]
    assert hook["secret"]


def test_list_omits_secret(auth_client):
    project, hook = _seed_webhook(auth_client)

    listing = auth_client.webhooks.list(project["id"])

    assert [h["id"] for h in listing] == [hook["id"]]
    assert "secret" not in listing[0]


def test_get_webhook(auth_client):
    _, hook = _seed_webhook(auth_client)

    fetched = auth_client.webhooks.get(hook["id"])

    assert fetched["id"] == hook["id"]


def test_update_webhook(auth_client):
    _, hook = _seed_webhook(auth_client)

    updated = auth_client.webhooks.update(
        hook["id"], is_active=False, events=["bug.resolved"],
    )

    assert updated["is_active"] is False
    assert updated["events"] == ["bug.resolved"]


def test_test_ping_returns_webhook(auth_client):
    _, hook = _seed_webhook(auth_client)

    result = auth_client.webhooks.test(hook["id"])

    assert result["id"] == hook["id"]


def test_list_deliveries_empty(auth_client):
    _, hook = _seed_webhook(auth_client)

    assert auth_client.webhooks.list_deliveries(hook["id"]) == []


def test_delete_webhook(auth_client):
    project, hook = _seed_webhook(auth_client)

    auth_client.webhooks.delete(hook["id"])

    assert auth_client.webhooks.list(project["id"]) == []
