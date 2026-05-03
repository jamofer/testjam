def test_create_version(auth_client, project_id):
    resp = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v1.0.0",
        "description": "First release",
        "vcs_tag": "v1.0.0",
        "status": "active",
    })

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "v1.0.0"
    assert data["vcs_tag"] == "v1.0.0"
    assert data["project_id"] == project_id


def test_list_versions(auth_client, project_id):
    auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "v1.0"})
    auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "v1.1"})

    resp = auth_client.get(f"/api/v1/projects/{project_id}/versions")

    assert resp.status_code == 200
    names = [v["name"] for v in resp.json()]
    assert "v1.0" in names and "v1.1" in names


def test_get_version(auth_client, project_id):
    version_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v2.0",
    }).json()["id"]

    resp = auth_client.get(f"/api/v1/versions/{version_id}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "v2.0"


def test_get_version_not_found(auth_client):
    resp = auth_client.get("/api/v1/versions/99999")

    assert resp.status_code == 404


def test_update_version_status(auth_client, project_id):
    version_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v3.0", "status": "active",
    }).json()["id"]

    resp = auth_client.put(f"/api/v1/versions/{version_id}", json={"status": "released"})

    assert resp.status_code == 200
    assert resp.json()["status"] == "released"


def test_delete_version(auth_client, project_id):
    version_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v0.1",
    }).json()["id"]

    auth_client.delete(f"/api/v1/versions/{version_id}")

    assert auth_client.get(f"/api/v1/versions/{version_id}").status_code == 404


def test_execution_linked_to_version(auth_client, project_id, case_ids):
    version_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v1.0",
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Versioned run",
        "type": "automatic",
        "version_id": version_id,
        "test_case_ids": case_ids,
    })

    assert resp.status_code == 201
    assert resp.json()["version_id"] == version_id
