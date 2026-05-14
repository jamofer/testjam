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


def test_bulk_delete_cases(auth_client, suite_id, case_ids):
    to_delete = case_ids[:2]
    resp = auth_client.post("/api/v1/cases/bulk-delete", json={"ids": to_delete})

    assert resp.status_code == 200
    assert resp.json()["deleted"] == 2

    remaining = auth_client.get(f"/api/v1/suites/{suite_id}/cases").json()
    remaining_ids = {c["id"] for c in remaining}
    assert all(cid not in remaining_ids for cid in to_delete)
    assert case_ids[2] in remaining_ids


def test_bulk_delete_empty_is_noop(auth_client):
    resp = auth_client.post("/api/v1/cases/bulk-delete", json={"ids": []})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0


def test_bulk_delete_ignores_missing_ids(auth_client, case_ids):
    resp = auth_client.post("/api/v1/cases/bulk-delete", json={"ids": [case_ids[0], 99999]})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1


def test_reorder_case_steps(auth_client, case_ids):
    case_id = case_ids[0]
    step_ids = []
    for i in range(3):
        sid = auth_client.post(f"/api/v1/cases/{case_id}/steps", json={
            "action": f"Step {i}", "order": i + 1,
        }).json()["id"]
        step_ids.append(sid)

    new_order = [step_ids[2], step_ids[0], step_ids[1]]
    resp = auth_client.post(f"/api/v1/cases/{case_id}/steps/reorder",
                            json={"step_ids": new_order})
    assert resp.status_code == 200
    assert [s["id"] for s in resp.json()] == new_order
    assert [s["order"] for s in resp.json()] == [1, 2, 3]


def test_reorder_rejects_foreign_step(auth_client, suite_id, case_ids):
    case_id = case_ids[0]
    other_case = case_ids[1]
    other_step = auth_client.post(f"/api/v1/cases/{other_case}/steps", json={
        "action": "Other", "order": 1,
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/cases/{case_id}/steps/reorder",
                            json={"step_ids": [other_step]})
    assert resp.status_code == 400


def test_reorder_unknown_case_returns_404(auth_client):
    resp = auth_client.post("/api/v1/cases/99999/steps/reorder", json={"step_ids": []})
    assert resp.status_code == 404


def test_replace_steps_creates_full_set(auth_client, case_ids):
    case_id = case_ids[0]

    resp = auth_client.post(f"/api/v1/cases/{case_id}/steps/replace", json={"steps": [
        {"action": "Setup", "step_type": "setup", "order": 1},
        {"action": "Do thing", "step_type": "action", "order": 2},
        {"action": "Cleanup", "step_type": "teardown", "order": 3},
    ]})

    assert resp.status_code == 200
    rows = resp.json()
    assert [s["action"] for s in rows] == ["Setup", "Do thing", "Cleanup"]
    assert [s["step_type"] for s in rows] == ["setup", "action", "teardown"]
    assert [s["order"] for s in rows] == [1, 2, 3]


def test_replace_steps_wipes_existing(auth_client, case_ids):
    case_id = case_ids[0]
    for i in range(3):
        auth_client.post(f"/api/v1/cases/{case_id}/steps", json={
            "action": f"Old {i}", "order": i + 1,
        })

    resp = auth_client.post(f"/api/v1/cases/{case_id}/steps/replace", json={"steps": [
        {"action": "Fresh", "step_type": "action", "order": 1},
    ]})

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["action"] == "Fresh"


def test_replace_steps_empty_clears_all(auth_client, case_ids):
    case_id = case_ids[0]
    auth_client.post(f"/api/v1/cases/{case_id}/steps", json={"action": "x", "order": 1})

    resp = auth_client.post(f"/api/v1/cases/{case_id}/steps/replace", json={"steps": []})

    assert resp.status_code == 200
    assert resp.json() == []
    assert auth_client.get(f"/api/v1/cases/{case_id}/steps").json() == []


def test_replace_steps_unknown_case_returns_404(auth_client):
    resp = auth_client.post("/api/v1/cases/99999/steps/replace", json={"steps": []})
    assert resp.status_code == 404


# ─── Search ───────────────────────────────────────────────────────────────────

def test_search_cases_by_name(auth_client, project_id, suite_id, case_ids):
    auth_client.put(f"/api/v1/cases/{case_ids[0]}", json={"name": "Login flow"})
    auth_client.put(f"/api/v1/cases/{case_ids[1]}", json={"name": "Signup flow"})

    resp = auth_client.get(f"/api/v1/projects/{project_id}/cases?q=login")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Login flow" in names
    assert "Signup flow" not in names


def test_search_cases_by_description(auth_client, project_id, suite_id, case_ids):
    auth_client.put(f"/api/v1/cases/{case_ids[0]}", json={"description": "checkout cart"})
    auth_client.put(f"/api/v1/cases/{case_ids[1]}", json={"description": "register user"})

    resp = auth_client.get(f"/api/v1/projects/{project_id}/cases?q=checkout")
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert case_ids[0] in ids
    assert case_ids[1] not in ids


def test_search_cases_filter_tags(auth_client, project_id, suite_id, case_ids):
    auth_client.put(f"/api/v1/cases/{case_ids[0]}", json={"tags": ["smoke", "login"]})
    auth_client.put(f"/api/v1/cases/{case_ids[1]}", json={"tags": ["regression"]})

    resp = auth_client.get(f"/api/v1/projects/{project_id}/cases?tags=smoke")
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert case_ids[0] in ids
    assert case_ids[1] not in ids


def test_search_cases_no_filters_returns_all(auth_client, project_id, suite_id, case_ids):
    resp = auth_client.get(f"/api/v1/projects/{project_id}/cases")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_search_cases_no_match_returns_empty(auth_client, project_id, suite_id, case_ids):
    resp = auth_client.get(f"/api/v1/projects/{project_id}/cases?q=zzznomatch")
    assert resp.status_code == 200
    assert resp.json() == []


# ─── Case reorder ─────────────────────────────────────────────────────────────

def test_reorder_cases_in_suite(auth_client, suite_id, case_ids):
    new = list(reversed(case_ids))
    resp = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases/reorder",
        json={"case_ids": new},
    )
    assert resp.status_code == 200
    assert [c["id"] for c in resp.json()] == new

    listed = auth_client.get(f"/api/v1/suites/{suite_id}/cases").json()
    assert [c["id"] for c in listed] == new


def test_reorder_cases_rejects_partial_set(auth_client, suite_id, case_ids):
    resp = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases/reorder",
        json={"case_ids": case_ids[:2]},
    )
    assert resp.status_code == 400
