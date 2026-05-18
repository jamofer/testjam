import pytest

from testjam_client.errors import Conflict


def test_find_or_create_version_idempotent(auth_client):
    project = auth_client.projects.find_or_create("Versioned")
    first = auth_client.versions.find_or_create(project["id"], "master-abc1234", tag="abc1234")
    second = auth_client.versions.find_or_create(project["id"], "master-abc1234", tag="abc1234")

    assert first["id"] == second["id"]
    assert first["name"] == "master-abc1234"


def test_create_duplicate_version_raises_conflict(auth_client):
    project = auth_client.projects.find_or_create("Conflicter")
    auth_client.versions.create(project["id"], "v1.0")

    with pytest.raises(Conflict):
        auth_client.versions.create(project["id"], "v1.0")


def test_find_or_create_recovers_from_concurrent_conflict(auth_client, monkeypatch):
    project = auth_client.projects.find_or_create("Racer")
    first = auth_client.versions.create(project["id"], "release-1.0")
    original_find = auth_client.versions.find_by_name
    calls = {"n": 0}

    def find_then_blank(project_id, name):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return original_find(project_id, name)

    monkeypatch.setattr(auth_client.versions, "find_by_name", find_then_blank)

    resolved = auth_client.versions.find_or_create(project["id"], "release-1.0")

    assert resolved["id"] == first["id"]
    assert calls["n"] == 2


def test_list_versions(auth_client):
    project = auth_client.projects.find_or_create("Lister")
    auth_client.versions.create(project["id"], "v1")
    auth_client.versions.create(project["id"], "v2")

    listed = auth_client.versions.list(project["id"])

    names = [v["name"] for v in listed]
    assert "v1" in names
    assert "v2" in names
