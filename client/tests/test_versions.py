def test_find_or_create_version_idempotent(auth_client):
    project = auth_client.projects.find_or_create("Versioned")
    first = auth_client.versions.find_or_create(project["id"], "master-abc1234", tag="abc1234")
    second = auth_client.versions.find_or_create(project["id"], "master-abc1234", tag="abc1234")

    assert first["id"] == second["id"]
    assert first["name"] == "master-abc1234"


def test_list_versions(auth_client):
    project = auth_client.projects.find_or_create("Lister")
    auth_client.versions.create(project["id"], "v1")
    auth_client.versions.create(project["id"], "v2")

    listed = auth_client.versions.list(project["id"])

    names = [v["name"] for v in listed]
    assert "v1" in names
    assert "v2" in names
