def test_get_case(auth_client, suite_id, case_ids):
    resp = auth_client.get(f"/api/v1/cases/{case_ids[0]}")

    assert resp.status_code == 200
    assert resp.json()["name"] == "TC-0"


def test_get_case_not_found(auth_client):
    resp = auth_client.get("/api/v1/cases/99999")

    assert resp.status_code == 404


def test_update_case_basic_fields(auth_client, suite_id, case_ids):
    resp = auth_client.put(f"/api/v1/cases/{case_ids[0]}", json={
        "name": "Renamed TC",
        "description": "Does login",
        "preconditions": "User exists",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Renamed TC"
    assert data["preconditions"] == "User exists"


def test_update_case_setup_teardown_external_id(auth_client, suite_id, case_ids):
    resp = auth_client.put(f"/api/v1/cases/{case_ids[0]}", json={
        "setup": "Login As Admin",
        "teardown": "Logout",
        "external_id": "tests/login.py::test_login",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["setup"] == "Login As Admin"
    assert data["teardown"] == "Logout"
    assert data["external_id"] == "tests/login.py::test_login"


def test_delete_case(auth_client, suite_id, case_ids):
    auth_client.delete(f"/api/v1/cases/{case_ids[0]}")

    assert auth_client.get(f"/api/v1/cases/{case_ids[0]}").status_code == 404


# ─── Steps ────────────────────────────────────────────────────────────────────

def test_create_action_step(auth_client, case_ids):
    resp = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": "Click login button",
        "expected_result": "Dashboard is shown",
        "order": 1,
        "step_type": "action",
    })

    assert resp.status_code == 201
    data = resp.json()
    assert data["step_type"] == "action"
    assert data["action"] == "Click login button"


def test_create_setup_step(auth_client, case_ids):
    resp = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": "Open browser",
        "order": 1,
        "step_type": "setup",
    })

    assert resp.status_code == 201
    assert resp.json()["step_type"] == "setup"


def test_create_teardown_step(auth_client, case_ids):
    resp = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": "Close browser",
        "order": 1,
        "step_type": "teardown",
    })

    assert resp.status_code == 201
    assert resp.json()["step_type"] == "teardown"


def test_default_step_type_is_action(auth_client, case_ids):
    resp = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": "Do something", "order": 1,
    })

    assert resp.json()["step_type"] == "action"


def test_update_step(auth_client, case_ids):
    step_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": "Original", "order": 1,
    }).json()["id"]

    resp = auth_client.put(f"/api/v1/cases/{case_ids[0]}/steps/{step_id}", json={
        "action": "Updated content", "step_type": "teardown",
    })

    assert resp.status_code == 200
    assert resp.json()["action"] == "Updated content"
    assert resp.json()["step_type"] == "teardown"


def test_delete_step(auth_client, case_ids):
    step_id = auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
        "action": "Step to delete", "order": 1,
    }).json()["id"]

    auth_client.delete(f"/api/v1/cases/{case_ids[0]}/steps/{step_id}")

    steps = auth_client.get(f"/api/v1/cases/{case_ids[0]}/steps").json()
    assert not any(s["id"] == step_id for s in steps)


def test_case_steps_returned_in_order(auth_client, case_ids):
    for order in [3, 1, 2]:
        auth_client.post(f"/api/v1/cases/{case_ids[0]}/steps", json={
            "action": f"Step {order}", "order": order,
        })

    steps = auth_client.get(f"/api/v1/cases/{case_ids[0]}/steps").json()

    assert [s["order"] for s in steps] == [1, 2, 3]
