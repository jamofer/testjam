import pytest


@pytest.fixture
def project(auth_client):
    return auth_client.projects.create("Rerun Project")


@pytest.fixture
def me(auth_client):
    return auth_client.users.me()


@pytest.fixture
def execution(auth_client, project):
    suite = auth_client.suites.create(project["id"], name="S")
    login = auth_client.cases.create(suite["id"], "login")
    logout = auth_client.cases.create(suite["id"], "logout")
    return auth_client.executions.create(
        project["id"], title="Nightly", test_case_ids=[login["id"], logout["id"]],
    )


@pytest.fixture
def finished_execution(auth_client, execution):
    results = {result["test_case_title"]: result for result in auth_client.executions.list_results(execution["id"])}
    auth_client.results.update(results["login"]["id"], status="passed")
    auth_client.results.update(results["logout"]["id"], status="failed")
    auth_client.executions.update(execution["id"], status="completed")
    return execution


def test_rerun_every_case_starts_a_new_execution(auth_client, finished_execution):
    rerun = auth_client.executions.rerun(finished_execution["id"])

    titles = sorted(result["test_case_title"] for result in auth_client.executions.list_results(rerun["id"]))
    assert rerun["id"] != finished_execution["id"]
    assert rerun["title"] == "Nightly"
    assert titles == ["login", "logout"]


def test_rerun_not_passed_skips_passed_cases(auth_client, finished_execution):
    rerun = auth_client.executions.rerun(finished_execution["id"], cases="not_passed")

    titles = [result["test_case_title"] for result in auth_client.executions.list_results(rerun["id"])]
    assert titles == ["logout"]


def test_assign_result_and_filter_by_assignee(auth_client, me, execution):
    results = auth_client.executions.list_results(execution["id"])

    assigned = auth_client.results.assign(results[0]["id"], me["id"])

    mine = auth_client.executions.list_results(execution["id"], assigned_to_id=me["id"])
    assert assigned["assigned_to_id"] == me["id"]
    assert [result["id"] for result in mine] == [results[0]["id"]]


def test_assign_none_unassigns_result(auth_client, me, execution):
    result = auth_client.executions.list_results(execution["id"])[0]
    auth_client.results.assign(result["id"], me["id"])

    unassigned = auth_client.results.assign(result["id"], None)

    assert unassigned["assigned_to_id"] is None
