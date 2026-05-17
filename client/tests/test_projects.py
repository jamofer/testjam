from testjam_client.errors import Conflict


def test_create_and_list_project(auth_client):
    project = auth_client.projects.create("Alpha")
    assert project["id"]
    assert project["name"] == "Alpha"

    listing = auth_client.projects.list()
    assert any(p["id"] == project["id"] for p in listing)


def test_find_or_create_returns_existing(auth_client):
    first = auth_client.projects.find_or_create("Bravo")
    second = auth_client.projects.find_or_create("Bravo")

    assert first["id"] == second["id"]


def test_get_project(auth_client):
    created = auth_client.projects.create("Charlie")

    fetched = auth_client.projects.get(created["id"])

    assert fetched["name"] == "Charlie"


def test_delete_project(auth_client):
    created = auth_client.projects.create("Delta")

    auth_client.projects.delete(created["id"])

    assert auth_client.projects.find_by_name("Delta") is None
