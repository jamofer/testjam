"""Case revision history: author tracking, snapshots, list/get endpoints."""


def test_create_case_records_initial_revision(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id, "description": "First version",
    }).json()["id"]

    revs = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()
    assert len(revs) == 1
    assert revs[0]["change_kind"] == "created"
    assert revs[0]["actor"]["username"] == "u"


def test_update_case_records_new_revision(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id,
    }).json()["id"]

    auth_client.put(f"/api/v1/cases/{case_id}", json={"description": "Updated text"})
    auth_client.put(f"/api/v1/cases/{case_id}", json={"description": "Updated again"})

    revs = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()
    assert [r["change_kind"] for r in revs] == ["updated", "updated", "created"]


def test_revision_snapshot_captures_full_definition(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id,
        "description": "Logging in", "tags": ["smoke"],
    }).json()["id"]
    auth_client.post(f"/api/v1/cases/{case_id}/steps", json={
        "action": "Open page", "step_type": "action", "order": 1,
    })

    revs = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()
    rev_id = revs[0]["id"]
    detail = auth_client.get(f"/api/v1/cases/{case_id}/revisions/{rev_id}").json()
    snap = detail["snapshot"]

    assert snap["name"] == "Login"
    assert snap["description"] == "Logging in"
    assert snap["tags"] == ["smoke"]
    assert len(snap["steps"]) == 1
    assert snap["steps"][0]["action"] == "Open page"


def test_step_changes_create_revisions(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id,
    }).json()["id"]

    s1 = auth_client.post(f"/api/v1/cases/{case_id}/steps", json={
        "action": "Step 1", "step_type": "action", "order": 1,
    }).json()
    auth_client.put(f"/api/v1/cases/{case_id}/steps/{s1['id']}", json={"action": "Step 1 edited"})
    auth_client.delete(f"/api/v1/cases/{case_id}/steps/{s1['id']}")

    revs = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()
    # created + 3 step ops
    assert len(revs) == 4
    assert revs[-1]["change_kind"] == "created"


def test_case_out_includes_authors(auth_client, suite_id):
    case = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id,
    }).json()
    assert case["created_by"]["username"] == "u"
    assert case["updated_by"]["username"] == "u"


def test_no_op_update_skips_new_revision(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id, "description": "v1", "tags": ["smoke"],
    }).json()["id"]

    auth_client.put(f"/api/v1/cases/{case_id}", json={"description": "v1", "tags": ["smoke"]})

    revs = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()
    assert len(revs) == 1
    assert revs[0]["change_kind"] == "created"


def test_reorder_with_same_order_skips_revision(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id,
    }).json()["id"]
    step_ids = [
        auth_client.post(f"/api/v1/cases/{case_id}/steps", json={
            "action": f"Step {i}", "order": i,
        }).json()["id"]
        for i in (1, 2)
    ]
    revs_before = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()

    auth_client.post(f"/api/v1/cases/{case_id}/steps/reorder", json={"step_ids": step_ids})

    revs_after = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()
    assert len(revs_after) == len(revs_before)


def test_bulk_replace_writes_single_revision(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id,
    }).json()["id"]
    initial_revs = len(auth_client.get(f"/api/v1/cases/{case_id}/revisions").json())

    resp = auth_client.post(f"/api/v1/cases/{case_id}/steps/replace", json={"steps": [
        {"action": "Open", "step_type": "setup", "order": 1},
        {"action": "Click", "step_type": "action", "order": 2},
        {"action": "Close", "step_type": "teardown", "order": 3},
    ]})

    assert resp.status_code == 200
    revs = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()
    assert len(revs) == initial_revs + 1
    assert revs[0]["change_kind"] == "updated"


def test_bulk_replace_same_payload_skips_revision(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "Login", "suite_id": suite_id,
    }).json()["id"]
    payload = {"steps": [{"action": "Open", "step_type": "setup", "order": 1}]}

    auth_client.post(f"/api/v1/cases/{case_id}/steps/replace", json=payload)
    revs_after_first = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()

    auth_client.post(f"/api/v1/cases/{case_id}/steps/replace", json=payload)
    revs_after_second = auth_client.get(f"/api/v1/cases/{case_id}/revisions").json()

    assert len(revs_after_second) == len(revs_after_first)


def test_get_revision_404_when_wrong_case(auth_client, suite_id):
    case_a = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "A", "suite_id": suite_id,
    }).json()["id"]
    case_b = auth_client.post(f"/api/v1/suites/{suite_id}/cases", json={
        "name": "B", "suite_id": suite_id,
    }).json()["id"]
    rev_a = auth_client.get(f"/api/v1/cases/{case_a}/revisions").json()[0]["id"]

    resp = auth_client.get(f"/api/v1/cases/{case_b}/revisions/{rev_a}")
    assert resp.status_code == 404
