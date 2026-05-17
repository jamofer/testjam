def _seed_case(auth_client, project_id):
    suite = auth_client.suites.find_or_create(project_id, "S")
    case = auth_client.cases.find_or_create(suite["id"], "TC")
    auth_client.cases.replace_steps(case["id"], [
        {"action": "do thing", "expected_result": "thing done"},
    ])
    return case


def test_create_execution_with_version(auth_client):
    project = auth_client.projects.find_or_create("Exec Project")
    version = auth_client.versions.find_or_create(project["id"], "master-abc1234")
    case = _seed_case(auth_client, project["id"])

    execution = auth_client.executions.create(
        project["id"],
        title="CI run",
        type="automatic",
        test_case_ids=[case["id"]],
        version_id=version["id"],
    )

    assert execution["title"] == "CI run"
    assert execution["version_id"] == version["id"]


def test_result_lifecycle(auth_client):
    project = auth_client.projects.find_or_create("Result Project")
    case = _seed_case(auth_client, project["id"])
    execution = auth_client.executions.create(
        project["id"], title="Run", type="manual", test_case_ids=[case["id"]],
    )
    [result] = auth_client.executions.list_results(execution["id"])

    auth_client.results.update(result["id"], status="passed")
    refreshed = auth_client.results.get(result["id"])

    assert refreshed["status"] == "passed"


def test_step_result_start_update_log(auth_client):
    project = auth_client.projects.find_or_create("Step Project")
    case = _seed_case(auth_client, project["id"])
    execution = auth_client.executions.create(
        project["id"], title="Run", type="manual", test_case_ids=[case["id"]],
    )
    [result] = auth_client.executions.list_results(execution["id"])
    step_id = auth_client.cases.get(case["id"])["steps"][0]["id"]

    started = auth_client.step_results.start(result["id"], step_id)
    auth_client.step_results.update(result["id"], started["id"], status="passed")
    log = auth_client.step_results.append_log(
        result["id"], started["id"], level="INFO", message="hello",
    )

    assert started["step_id"] == step_id
    assert log["step_result_id"] == started["id"]
    assert log["appended"] >= 1
