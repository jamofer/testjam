"""Additional execution cases not covered by test_executions.py."""


def test_update_execution_status(auth_client, project_id, case_ids):
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Run", "type": "manual", "test_case_ids": case_ids,
    }).json()["id"]

    resp = auth_client.put(f"/api/v1/executions/{exec_id}", json={"status": "completed"})

    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_delete_execution(auth_client, project_id, case_ids):
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Del", "type": "manual", "test_case_ids": case_ids,
    }).json()["id"]

    auth_client.delete(f"/api/v1/executions/{exec_id}")

    assert auth_client.get(f"/api/v1/executions/{exec_id}").status_code == 404


def test_list_executions_filter_by_status(auth_client, project_id, case_ids):
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R", "type": "manual", "test_case_ids": case_ids,
    }).json()["id"]
    auth_client.put(f"/api/v1/executions/{exec_id}", json={"status": "completed"})
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Pending", "type": "manual", "test_case_ids": case_ids,
    })

    resp = auth_client.get(f"/api/v1/projects/{project_id}/executions?status=completed")

    assert all(e["status"] == "completed" for e in resp.json())


def test_list_executions_filter_by_type(auth_client, project_id, case_ids):
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Manual", "type": "manual", "test_case_ids": case_ids,
    })
    auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "Auto", "type": "automatic", "test_case_ids": case_ids,
    })

    resp = auth_client.get(f"/api/v1/projects/{project_id}/executions?type=automatic")

    assert all(e["type"] == "automatic" for e in resp.json())


def test_update_result(auth_client, project_id, case_ids):
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R", "type": "manual", "test_case_ids": case_ids,
    }).json()["id"]
    result_id = auth_client.post(f"/api/v1/executions/{exec_id}/results", json={
        "test_case_id": case_ids[0], "status": "not_run",
    }).json()["id"]

    resp = auth_client.put(f"/api/v1/results/{result_id}", json={
        "status": "failed", "comment": "Assertion failed at step 2",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "failed"
    assert data["comment"] == "Assertion failed at step 2"


def test_step_result_with_log_output(auth_client, project_id, suite_id, case_ids):
    step_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "content": "Click login", "order": 1, "step_type": "action",
    }).json()["id"]
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R", "type": "automatic", "test_case_ids": case_ids,
    }).json()["id"]
    result_id = auth_client.post(f"/api/v1/executions/{exec_id}/results", json={
        "test_case_id": case_ids[0],
        "status": "failed",
        "step_results": [{"step_id": step_id, "status": "failed", "log_output": "**[FAIL]** Element not found"}],
    }).json()["id"]

    resp = auth_client.get(f"/api/v1/results/{result_id}")

    step_results = resp.json()["step_results"]
    assert len(step_results) == 1
    assert step_results[0]["log_output"] == "**[FAIL]** Element not found"
    assert step_results[0]["status"] == "failed"


def test_update_step_result_log_output(auth_client, project_id, suite_id, case_ids):
    step_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "content": "Step", "order": 1,
    }).json()["id"]
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R", "type": "automatic", "test_case_ids": case_ids,
    }).json()["id"]
    result = auth_client.post(f"/api/v1/executions/{exec_id}/results", json={
        "test_case_id": case_ids[0], "status": "not_run",
        "step_results": [{"step_id": step_id, "status": "not_run"}],
    }).json()
    sr_id = result["step_results"][0]["id"]

    resp = auth_client.put(f"/api/v1/results/{result['id']}/step-results/{sr_id}", json={
        "status": "passed",
        "log_output": "**[INFO]** Login successful",
    })

    assert resp.status_code == 200
    assert resp.json()["log_output"] == "**[INFO]** Login successful"
