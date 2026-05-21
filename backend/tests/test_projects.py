def test_create_and_list_project(auth_client):
    resp = auth_client.post("/api/v1/projects", json={"name": "My Project"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = auth_client.get("/api/v1/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert project_id in ids


def test_create_project_with_duplicate_name_returns_409(auth_client):
    auth_client.post("/api/v1/projects", json={"name": "Duplicate"})

    resp = auth_client.post("/api/v1/projects", json={"name": "Duplicate"})

    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


def test_create_project_race_translates_integrity_error_to_409(auth_client, monkeypatch):
    from testjam.routers import projects as projects_router

    auth_client.post("/api/v1/projects", json={"name": "Racer"})
    monkeypatch.setattr(projects_router, "_find_project_by_name", lambda db, name: None)

    resp = auth_client.post("/api/v1/projects", json={"name": "Racer"})

    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


def test_create_suite_and_case(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]

    suite = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "Suite A"})
    assert suite.status_code == 201
    suite_id = suite.json()["id"]

    case = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={"name": "TC-001", "suite_id": suite_id})
    assert case.status_code == 201
    assert case.json()["name"] == "TC-001"


def test_delete_project(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "ToDelete"}).json()["id"]
    resp = auth_client.delete(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 204
    resp = auth_client.get(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 404
