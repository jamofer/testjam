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


def test_list_child_suites_by_parent_id(auth_client, project_id, suite_id):
    child_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child A", "parent_suite_id": suite_id,
    }).json()["id"]
    auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Sibling", "parent_suite_id": suite_id,
    })

    resp = auth_client.get(f"/api/v1/projects/{project_id}/suites", params={"parent_suite_id": suite_id})

    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert child_id in ids
    assert suite_id not in ids  # root suite itself should not appear


def test_duplicate_child_suite_rejected(auth_client, project_id, suite_id):
    auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child", "parent_suite_id": suite_id,
    })
    resp = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child", "parent_suite_id": suite_id,
    })
    assert resp.status_code == 409


def test_reorder_suite_steps(auth_client, suite_id):
    step_ids = []
    for i in range(3):
        sid = auth_client.post(f"/api/v1/suites/{suite_id}/steps", json={
            "action": f"Setup {i}", "step_type": "setup", "order": i + 1,
        }).json()["id"]
        step_ids.append(sid)

    new_order = [step_ids[2], step_ids[0], step_ids[1]]
    resp = auth_client.post(f"/api/v1/suites/{suite_id}/steps/reorder",
                            json={"step_ids": new_order})
    assert resp.status_code == 200
    returned_ids = [s["id"] for s in resp.json() if s["step_type"] == "setup"]
    assert returned_ids == new_order
    assert [s["order"] for s in resp.json() if s["step_type"] == "setup"] == [1, 2, 3]


def test_reorder_suite_steps_rejects_foreign_step(auth_client, project_id, suite_id):
    other_suite_id = auth_client.post(f"/api/v1/projects/{project_id}/suites",
                                      json={"name": "Other"}).json()["id"]
    foreign_step = auth_client.post(f"/api/v1/suites/{other_suite_id}/steps", json={
        "action": "Foreign", "step_type": "setup", "order": 1,
    }).json()["id"]

    resp = auth_client.post(f"/api/v1/suites/{suite_id}/steps/reorder",
                            json={"step_ids": [foreign_step]})
    assert resp.status_code == 400


def test_reorder_suite_steps_unknown_suite(auth_client):
    resp = auth_client.post("/api/v1/suites/99999/steps/reorder", json={"step_ids": []})
    assert resp.status_code == 404


# ─── Suite reorder (siblings) ─────────────────────────────────────────────────

def test_reorder_top_level_suites(auth_client, project_id):
    s_a = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "A"}).json()["id"]
    s_b = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "B"}).json()["id"]
    s_c = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "C"}).json()["id"]

    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/suites/reorder",
        json={"suite_ids": [s_c, s_a, s_b]},
    )
    assert resp.status_code == 200
    assert [s["id"] for s in resp.json()] == [s_c, s_a, s_b]

    listed = auth_client.get(f"/api/v1/projects/{project_id}/suites").json()
    assert [s["id"] for s in listed] == [s_c, s_a, s_b]


def test_reorder_child_suites_only_affects_siblings(auth_client, project_id):
    parent = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "P"}).json()["id"]
    c1 = auth_client.post(f"/api/v1/projects/{project_id}/suites",
                          json={"name": "c1", "parent_suite_id": parent}).json()["id"]
    c2 = auth_client.post(f"/api/v1/projects/{project_id}/suites",
                          json={"name": "c2", "parent_suite_id": parent}).json()["id"]

    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/suites/reorder",
        params={"parent_suite_id": parent},
        json={"suite_ids": [c2, c1]},
    )
    assert resp.status_code == 200
    assert [s["id"] for s in resp.json()] == [c2, c1]


def test_delete_suite_cascades_children_and_cases(auth_client, project_id, suite_id):
    child_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child", "parent_suite_id": suite_id,
    }).json()["id"]
    grandchild_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Grandchild", "parent_suite_id": child_id,
    }).json()["id"]
    case_id = auth_client.post(f"/api/v1/suites/{grandchild_id}/cases", json={
        "name": "TC", "suite_id": grandchild_id,
    }).json()["id"]

    resp = auth_client.delete(f"/api/v1/suites/{suite_id}")

    assert resp.status_code == 204
    assert auth_client.get(f"/api/v1/suites/{child_id}").status_code == 404
    assert auth_client.get(f"/api/v1/suites/{grandchild_id}").status_code == 404
    assert auth_client.get(f"/api/v1/cases/{case_id}").status_code == 404


def test_delete_suite_impact_counts_results(auth_client, project_id, suite_id):
    child_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child", "parent_suite_id": suite_id,
    }).json()["id"]
    case_a = auth_client.post(f"/api/v1/suites/{suite_id}/cases",
                              json={"name": "A", "suite_id": suite_id}).json()["id"]
    case_b = auth_client.post(f"/api/v1/suites/{child_id}/cases",
                              json={"name": "B", "suite_id": child_id}).json()["id"]
    exec_id = auth_client.post(f"/api/v1/projects/{project_id}/executions", json={
        "title": "R", "type": "manual", "test_case_ids": [case_a, case_b],
    }).json()["id"]

    resp = auth_client.get(f"/api/v1/suites/{suite_id}/delete-impact")

    assert resp.status_code == 200
    body = resp.json()
    assert body["suite_count"] == 2
    assert body["case_count"] == 2
    assert body["result_count"] == 2
    assert body["execution_count"] == 1
    assert exec_id


def test_delete_suite_impact_zero_for_empty(auth_client, suite_id):
    resp = auth_client.get(f"/api/v1/suites/{suite_id}/delete-impact")

    assert resp.status_code == 200
    body = resp.json()
    assert body["case_count"] == 0
    assert body["result_count"] == 0
    assert body["execution_count"] == 0


def test_archive_suite_archives_subtree_cases(auth_client, project_id, suite_id):
    child_id = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={
        "name": "Child", "parent_suite_id": suite_id,
    }).json()["id"]
    case_a = auth_client.post(f"/api/v1/suites/{suite_id}/cases",
                              json={"name": "A", "suite_id": suite_id}).json()["id"]
    case_b = auth_client.post(f"/api/v1/suites/{child_id}/cases",
                              json={"name": "B", "suite_id": child_id}).json()["id"]

    resp = auth_client.post(f"/api/v1/suites/{suite_id}/archive")

    assert resp.status_code == 200
    assert resp.json() == {"suite_count": 2, "archived_case_count": 2}
    assert auth_client.get(f"/api/v1/cases/{case_a}").json()["archived_at"] is not None
    assert auth_client.get(f"/api/v1/cases/{case_b}").json()["archived_at"] is not None


def test_archive_suite_skips_already_archived(auth_client, suite_id):
    case_id = auth_client.post(f"/api/v1/suites/{suite_id}/cases",
                               json={"name": "A", "suite_id": suite_id}).json()["id"]
    auth_client.post(f"/api/v1/cases/{case_id}/archive")

    resp = auth_client.post(f"/api/v1/suites/{suite_id}/archive")

    assert resp.status_code == 200
    assert resp.json()["archived_case_count"] == 0


def test_reorder_suites_rejects_partial_set(auth_client, project_id):
    s_a = auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "A"}).json()["id"]
    auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "B"})
    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/suites/reorder",
        json={"suite_ids": [s_a]},
    )
    assert resp.status_code == 400
