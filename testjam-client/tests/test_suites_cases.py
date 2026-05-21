def test_suite_and_case_round_trip(auth_client):
    project = auth_client.projects.find_or_create("Suite Project")
    suite = auth_client.suites.find_or_create(project["id"], "Auth")
    case = auth_client.cases.find_or_create(suite["id"], "Login flow")

    assert suite["project_id"] == project["id"]
    assert case["suite_id"] == suite["id"]


def test_replace_steps(auth_client):
    project = auth_client.projects.find_or_create("Steps Project")
    suite = auth_client.suites.find_or_create(project["id"], "Auth")
    case = auth_client.cases.find_or_create(suite["id"], "Login")

    steps = auth_client.cases.replace_steps(case["id"], [
        {"action": "open page", "expected_result": "form visible"},
        {"action": "submit", "expected_result": "redirect"},
    ])

    assert len(steps) == 2
    assert steps[0]["action"] == "open page"


def test_step_crud_with_setup_and_teardown(auth_client):
    project = auth_client.projects.find_or_create("Crud Steps")
    suite = auth_client.suites.find_or_create(project["id"], "S")
    case = auth_client.cases.find_or_create(suite["id"], "C")

    setup = auth_client.cases.add_step(case["id"], "spin up db", step_type="setup")
    main = auth_client.cases.add_step(case["id"], "click button")
    teardown = auth_client.cases.add_step(case["id"], "tear down", step_type="teardown")

    listed = auth_client.cases.list_steps(case["id"])
    assert {s["step_type"] for s in listed} == {"setup", "action", "teardown"}

    auth_client.cases.update_step(case["id"], main["id"], action="click big button")
    updated = [s for s in auth_client.cases.list_steps(case["id"]) if s["id"] == main["id"]]
    assert updated[0]["action"] == "click big button"

    auth_client.cases.delete_step(case["id"], teardown["id"])
    after_delete = auth_client.cases.list_steps(case["id"])
    assert teardown["id"] not in [s["id"] for s in after_delete]

    auth_client.cases.delete_steps_by_type(case["id"], "setup")
    remaining = auth_client.cases.list_steps(case["id"])
    assert all(s["step_type"] != "setup" for s in remaining)


def test_reorder_steps(auth_client):
    project = auth_client.projects.find_or_create("Reorder")
    suite = auth_client.suites.find_or_create(project["id"], "S")
    case = auth_client.cases.find_or_create(suite["id"], "C")
    a = auth_client.cases.add_step(case["id"], "A")
    b = auth_client.cases.add_step(case["id"], "B")
    c = auth_client.cases.add_step(case["id"], "C")

    reordered = auth_client.cases.reorder_steps(case["id"], [c["id"], a["id"], b["id"]])

    assert [s["id"] for s in reordered] == [c["id"], a["id"], b["id"]]
