"""Test plan SDK coverage."""


def _seed_cases(auth_client, project_id, count=2):
    suite = auth_client.suites.find_or_create(project_id, "S")
    return [
        auth_client.cases.find_or_create(suite["id"], f"C{i}")
        for i in range(count)
    ]


def test_create_plan_with_cases(auth_client):
    project = auth_client.projects.find_or_create("PlanProj")
    cases = _seed_cases(auth_client, project["id"])

    plan = auth_client.plans.create(
        project["id"],
        "Smoke",
        description="P0 suite",
        test_case_ids=[c["id"] for c in cases],
    )

    assert plan["title"] == "Smoke"
    assert plan["description"] == "P0 suite"
    assert set(plan["test_case_ids"]) == {c["id"] for c in cases}


def test_list_plans(auth_client):
    project = auth_client.projects.find_or_create("PlanProj")
    auth_client.plans.create(project["id"], "A")
    auth_client.plans.create(project["id"], "B")

    listing = auth_client.plans.list(project["id"])

    assert {p["title"] for p in listing} == {"A", "B"}


def test_get_plan(auth_client):
    project = auth_client.projects.find_or_create("PlanProj")
    created = auth_client.plans.create(project["id"], "Solo")

    fetched = auth_client.plans.get(created["id"])

    assert fetched["id"] == created["id"]


def test_update_plan_replaces_cases(auth_client):
    project = auth_client.projects.find_or_create("PlanProj")
    cases = _seed_cases(auth_client, project["id"], count=3)
    plan = auth_client.plans.create(
        project["id"], "P", test_case_ids=[cases[0]["id"]],
    )

    updated = auth_client.plans.update(
        plan["id"],
        title="Renamed",
        test_case_ids=[cases[1]["id"], cases[2]["id"]],
    )

    assert updated["title"] == "Renamed"
    assert set(updated["test_case_ids"]) == {cases[1]["id"], cases[2]["id"]}


def test_add_cases_appends(auth_client):
    project = auth_client.projects.find_or_create("PlanProj")
    cases = _seed_cases(auth_client, project["id"], count=2)
    plan = auth_client.plans.create(
        project["id"], "P", test_case_ids=[cases[0]["id"]],
    )

    grown = auth_client.plans.add_cases(plan["id"], [cases[1]["id"]])

    assert set(grown["test_case_ids"]) == {cases[0]["id"], cases[1]["id"]}


def test_delete_plan(auth_client):
    project = auth_client.projects.find_or_create("PlanProj")
    plan = auth_client.plans.create(project["id"], "P")

    auth_client.plans.delete(plan["id"])

    assert auth_client.plans.list(project["id"]) == []
