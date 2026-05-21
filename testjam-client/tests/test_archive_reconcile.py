"""Archive endpoints + reconcile workflow."""


def _seed(auth_client):
    project = auth_client.projects.find_or_create("Reconcile")
    suite = auth_client.suites.find_or_create(project["id"], "S")
    return project, suite


def test_archive_hides_case_from_default_list(auth_client):
    _, suite = _seed(auth_client)
    case = auth_client.cases.find_or_create(suite["id"], "C", external_id="ext-1")

    auth_client.cases.archive(case["id"])

    assert auth_client.cases.list(suite["id"]) == []
    with_hidden = auth_client.cases.list(suite["id"], include_archived=True)
    assert len(with_hidden) == 1
    assert with_hidden[0]["archived_at"] is not None


def test_unarchive_restores_visibility(auth_client):
    _, suite = _seed(auth_client)
    case = auth_client.cases.find_or_create(suite["id"], "C", external_id="ext-1")
    auth_client.cases.archive(case["id"])

    auth_client.cases.unarchive(case["id"])

    listing = auth_client.cases.list(suite["id"])
    assert len(listing) == 1
    assert listing[0]["archived_at"] is None


def test_reconcile_creates_updates_and_archives(auth_client):
    _, suite = _seed(auth_client)
    existing = auth_client.cases.create(
        suite["id"], "Old name", external_id="keep", description="old",
    )
    stale = auth_client.cases.create(
        suite["id"], "Goes away", external_id="dead",
    )

    diff = auth_client.cases.reconcile(suite["id"], specs=[
        {"external_id": "keep", "name": "New name", "description": "new",
         "steps": [{"action": "do thing", "expected_result": "thing done"}]},
        {"external_id": "fresh", "name": "Brand new",
         "steps": [{"action": "setup", "step_type": "setup"},
                    {"action": "act"}]},
    ])

    assert existing["id"] in diff["updated"]
    assert stale["id"] in diff["archived"]
    assert len(diff["created"]) == 1

    refreshed = auth_client.cases.get(existing["id"])
    assert refreshed["name"] == "New name"
    assert refreshed["description"] == "new"
    assert [s["action"] for s in refreshed["steps"]] == ["do thing"]

    by_external = {
        c["external_id"]: c
        for c in auth_client.cases.list(suite["id"], include_archived=True)
    }
    assert by_external["dead"]["archived_at"] is not None
    assert by_external["fresh"]["archived_at"] is None
    assert len(by_external["fresh"]["steps"]) == 2


def test_reconcile_is_idempotent(auth_client):
    _, suite = _seed(auth_client)
    specs = [
        {"external_id": "a", "name": "A",
         "steps": [{"action": "step"}]},
    ]

    first = auth_client.cases.reconcile(suite["id"], specs=specs)
    second = auth_client.cases.reconcile(suite["id"], specs=specs)

    assert len(first["created"]) == 1
    assert second == {"created": [], "updated": [], "archived": []}
