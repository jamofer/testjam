import pytest


@pytest.fixture
def suite_chain(auth_client, project_id):
    root_id = _create_suite(auth_client, project_id, "Root")
    child_id = _create_suite(auth_client, project_id, "Child", parent_suite_id=root_id)
    grandchild_id = _create_suite(auth_client, project_id, "Grandchild", parent_suite_id=child_id)
    return root_id, child_id, grandchild_id


@pytest.fixture
def foreign_suite_id(auth_client):
    other_project_id = auth_client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    return _create_suite(auth_client, other_project_id, "Foreign")


def test_suite_cannot_become_its_own_parent(auth_client, suite_chain):
    root_id, _, _ = suite_chain

    response = auth_client.put(f"/api/v1/suites/{root_id}", json={"parent_suite_id": root_id})

    assert response.status_code == 422


def test_suite_cannot_move_under_its_descendant(auth_client, suite_chain):
    root_id, _, grandchild_id = suite_chain

    response = auth_client.put(f"/api/v1/suites/{root_id}", json={"parent_suite_id": grandchild_id})

    assert response.status_code == 422
    assert auth_client.get(f"/api/v1/suites/{root_id}").json()["parent_suite_id"] is None


def test_suite_can_move_under_a_sibling_branch(auth_client, project_id, suite_chain):
    _, child_id, _ = suite_chain
    other_root_id = _create_suite(auth_client, project_id, "Other root")

    response = auth_client.put(f"/api/v1/suites/{child_id}", json={"parent_suite_id": other_root_id})

    assert response.status_code == 200
    assert response.json()["parent_suite_id"] == other_root_id


def test_suite_cannot_move_under_another_projects_suite(auth_client, suite_chain, foreign_suite_id):
    root_id, _, _ = suite_chain

    response = auth_client.put(f"/api/v1/suites/{root_id}", json={"parent_suite_id": foreign_suite_id})

    assert response.status_code == 422


def test_suite_cannot_be_created_under_another_projects_suite(auth_client, project_id, foreign_suite_id):
    response = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "Child", "parent_suite_id": foreign_suite_id},
    )

    assert response.status_code == 422


def _create_suite(client, project_id: int, name: str, parent_suite_id: int | None = None) -> int:
    return client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": name, "parent_suite_id": parent_suite_id},
    ).json()["id"]
