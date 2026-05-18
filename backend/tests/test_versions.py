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


def test_create_version_with_release_date(auth_client, project_id):
    resp = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v4.0", "release_date": "2026-06-01",
    })

    assert resp.status_code == 201
    body = resp.json()
    assert body["release_date"] == "2026-06-01"
    assert body["released_at"] is None


def test_released_at_set_on_status_transition(auth_client, project_id):
    version_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v5.0",
    }).json()["id"]
    assert auth_client.get(f"/api/v1/versions/{version_id}").json()["released_at"] is None

    auth_client.put(f"/api/v1/versions/{version_id}", json={"status": "released"})
    released = auth_client.get(f"/api/v1/versions/{version_id}").json()

    assert released["status"] == "released"
    assert released["released_at"] is not None


def test_released_at_cleared_when_status_reverts(auth_client, project_id):
    version_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v6.0", "status": "released",
    }).json()["id"]
    assert auth_client.get(f"/api/v1/versions/{version_id}").json()["released_at"] is not None

    auth_client.put(f"/api/v1/versions/{version_id}", json={"status": "active"})

    assert auth_client.get(f"/api/v1/versions/{version_id}").json()["released_at"] is None


def test_execution_with_version_string_autocreates_version(auth_client, project_id, case_ids):
    resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Auto v",
        "type": "automatic",
        "version": "v7.0",
        "test_case_ids": case_ids,
    })

    assert resp.status_code == 201
    created_version_id = resp.json()["version_id"]
    assert created_version_id is not None
    listed = auth_client.get(f"/api/v1/projects/{project_id}/versions").json()
    assert any(v["id"] == created_version_id and v["name"] == "v7.0" and v["status"] == "active" for v in listed)


def test_execution_with_version_string_reuses_existing(auth_client, project_id, case_ids):
    existing_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={
        "name": "v8.0",
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Reuse v",
        "type": "automatic",
        "version": "V8.0",
        "test_case_ids": case_ids,
    })

    assert resp.status_code == 201
    assert resp.json()["version_id"] == existing_id


def test_duplicate_version_name_returns_conflict(auth_client, project_id):
    first = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "dup-1.0"})

    second = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "dup-1.0"})

    assert first.status_code == 201
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


def test_duplicate_version_name_allowed_across_projects(auth_client, project_id):
    other_project_id = auth_client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]

    a = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "shared-1.0"})
    b = auth_client.post(f"/api/v1/projects/{other_project_id}/versions", json={"name": "shared-1.0"})

    assert a.status_code == 201
    assert b.status_code == 201


def test_update_version_to_existing_name_returns_conflict(auth_client, project_id):
    auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "rename-a"})
    second_id = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "rename-b"}).json()["id"]

    resp = auth_client.put(f"/api/v1/versions/{second_id}", json={"name": "rename-a"})

    assert resp.status_code == 409


def test_list_executions_filtered_by_version(auth_client, project_id, case_ids):
    v1 = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "v1.0"}).json()["id"]
    v2 = auth_client.post(f"/api/v1/projects/{project_id}/versions", json={"name": "v2.0"}).json()["id"]
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run A", "type": "manual", "version_id": v1, "test_case_ids": case_ids,
    })
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run B", "type": "manual", "version_id": v2, "test_case_ids": case_ids,
    })
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run C", "type": "manual", "test_case_ids": case_ids,
    })

    resp = auth_client.get(f"/api/v1/projects/{project_id}/executions", params={"version_id": v1})

    assert resp.status_code == 200
    titles = [ex["title"] for ex in resp.json()]
    assert titles == ["Run A"]
