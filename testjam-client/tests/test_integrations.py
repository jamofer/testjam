"""SDK integrations resource end-to-end against the in-process API."""
import pytest

from testjam.services.integrations.providers.fake import instance as fake_provider


@pytest.fixture(autouse=True)
def _reset_fake():
    fake_provider().reset()
    yield
    fake_provider().reset()


def _bootstrap_project(auth_client, name="Integrated"):
    project = auth_client.projects.find_or_create(name)
    return project["id"]


def _seed_case_and_result(auth_client, project_id):
    suite = auth_client.suites.find_or_create(project_id, "S")
    case = auth_client.cases.find_or_create(suite["id"], "TC")
    auth_client.cases.replace_steps(case["id"], [
        {"action": "do thing", "expected_result": "ok"},
    ])
    execution = auth_client.executions.create(
        project_id, title="Run", type="manual", test_case_ids=[case["id"]],
    )
    [result] = auth_client.executions.list_results(execution["id"])
    return result


def test_list_providers_includes_fake(auth_client):
    providers = auth_client.integrations.list_providers()

    keys = {provider["key"] for provider in providers}
    assert "fake" in keys


def test_create_list_update_delete_integration(auth_client):
    project_id = _bootstrap_project(auth_client, "CRUD")
    created = auth_client.integrations.create(
        project_id,
        provider="fake", name="Primary",
        config={"project_key": "DEMO"}, secret="tok",
    )

    listed = auth_client.integrations.list(project_id)
    assert [item["id"] for item in listed] == [created["id"]]

    updated = auth_client.integrations.update(created["id"], name="Renamed")
    assert updated["name"] == "Renamed"

    auth_client.integrations.delete(created["id"])
    assert auth_client.integrations.list(project_id) == []


def test_push_and_sync_external_link(auth_client):
    project_id = _bootstrap_project(auth_client, "Push")
    integration = auth_client.integrations.create(
        project_id,
        provider="fake", name="Tracker",
        config={"project_key": "DEMO"}, secret="tok",
    )
    bug = auth_client.request(
        "POST", f"/projects/{project_id}/bugs", json={"title": "Crash"},
    ).json()

    link = auth_client.integrations.push_bug(
        bug["id"], integration_id=integration["id"],
    )

    assert link["provider"] == "fake"
    fake_provider().set_remote_status(link["external_id"], "Closed")

    synced = auth_client.integrations.sync_bug_link(bug["id"], link["id"])

    assert synced["status_raw"] == "Closed"
    assert synced["status_normalized"] == "closed"


def test_report_from_result_creates_bug_and_optional_link(auth_client):
    project_id = _bootstrap_project(auth_client, "Reporter")
    result = _seed_case_and_result(auth_client, project_id)
    integration = auth_client.integrations.create(
        project_id,
        provider="fake", name="Tracker",
        config={"project_key": "DEMO"}, secret="tok",
    )

    response = auth_client.integrations.report_from_result(
        result["id"],
        title="Flaky login", description="trace…",
        integration_id=integration["id"], labels=["flaky"],
    )

    assert response["bug_id"] > 0
    assert response["external_link"]["provider"] == "fake"
