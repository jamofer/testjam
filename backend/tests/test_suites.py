def test_get_suite(auth_client, project_id, suite_id):
    resp = auth_client.get(f"/api/v1/suites/{suite_id}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Suite A"


def test_get_suite_not_found(auth_client):
    resp = auth_client.get("/api/v1/suites/99999")

    assert resp.status_code == 404


def test_update_suite_title(auth_client, project_id, suite_id):
    resp = auth_client.put(f"/api/v1/suites/{suite_id}", json={"name": "Renamed Suite"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Suite"


def test_update_suite_setup_and_teardown(auth_client, project_id, suite_id):
    resp = auth_client.put(f"/api/v1/suites/{suite_id}", json={
        "setup": "Open Browser    ${URL}",
        "teardown": "Close Browser",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["setup"] == "Open Browser    ${URL}"
    assert data["teardown"] == "Close Browser"


def test_delete_suite(auth_client, project_id):
    sid = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "ToDelete"}).json()["id"]

    auth_client.delete(f"/api/v1/suites/{sid}")

    assert auth_client.get(f"/api/v1/suites/{sid}").status_code == 404


def test_create_nested_suite(auth_client, project_id, suite_id):
    resp = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child Suite", "parent_suite_id": suite_id,
    })

    assert resp.status_code == 201
    parent = auth_client.get(f"/api/v1/suites/{suite_id}").json()
    assert resp.json()["id"] in parent["child_suite_ids"]


def test_list_suites_returns_only_root(auth_client, project_id, suite_id):
    child_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child", "parent_suite_id": suite_id,
    }).json()["id"]

    resp = auth_client.get(f"/api/v1/projects/{project_id}/suites")

    root_ids = [s["id"] for s in resp.json()]
    assert suite_id in root_ids
    assert child_id not in root_ids
