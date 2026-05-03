def test_create_plan_with_cases(auth_client, project_id, case_ids):
    resp = auth_client.post(f"/api/v1/projects/{project_id}/plans", json={
        "title": "Smoke Plan",
        "description": "Basic smoke tests",
        "test_case_ids": case_ids,
    })

    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Smoke Plan"
    assert set(data["test_case_ids"]) == set(case_ids)


def test_list_plans(auth_client, project_id, case_ids):
    auth_client.post(f"/api/v1/projects/{project_id}/plans", json={"title": "Plan A"})
    auth_client.post(f"/api/v1/projects/{project_id}/plans", json={"title": "Plan B"})

    resp = auth_client.get(f"/api/v1/projects/{project_id}/plans")

    assert resp.status_code == 200
    titles = [p["title"] for p in resp.json()]
    assert "Plan A" in titles and "Plan B" in titles


def test_get_plan(auth_client, project_id, case_ids):
    plan_id = auth_client.post(f"/api/v1/projects/{project_id}/plans", json={
        "title": "My Plan", "test_case_ids": case_ids[:2],
    }).json()["id"]

    resp = auth_client.get(f"/api/v1/plans/{plan_id}")

    assert resp.status_code == 200
    assert len(resp.json()["test_case_ids"]) == 2


def test_get_plan_not_found(auth_client):
    resp = auth_client.get("/api/v1/plans/99999")

    assert resp.status_code == 404


def test_update_plan_cases(auth_client, project_id, case_ids):
    plan_id = auth_client.post(f"/api/v1/projects/{project_id}/plans", json={
        "title": "Plan", "test_case_ids": case_ids[:1],
    }).json()["id"]

    resp = auth_client.put(f"/api/v1/plans/{plan_id}", json={"test_case_ids": case_ids})

    assert resp.status_code == 200
    assert set(resp.json()["test_case_ids"]) == set(case_ids)


def test_delete_plan(auth_client, project_id):
    plan_id = auth_client.post(f"/api/v1/projects/{project_id}/plans", json={"title": "Del"}).json()["id"]

    auth_client.delete(f"/api/v1/plans/{plan_id}")

    assert auth_client.get(f"/api/v1/plans/{plan_id}").status_code == 404


def test_create_execution_from_plan(auth_client, project_id, case_ids):
    plan_id = auth_client.post(f"/api/v1/projects/{project_id}/plans", json={
        "title": "Plan", "test_case_ids": case_ids,
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "From Plan", "type": "manual", "test_plan_id": plan_id, "test_case_ids": case_ids,
    })

    assert resp.status_code == 201
    assert resp.json()["summary"]["total"] == len(case_ids)
