import pytest

from testjam.auth.security import hash_password
from testjam.models.user import User
from tests.conftest import TestingSession


@pytest.fixture
def execution_with_result(auth_client):
    project_id = auth_client.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    suite_id = auth_client.post(
        f"/api/v1/projects/{project_id}/suites", json={"name": "S"},
    ).json()["id"]
    case_id = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases", json={"name": "C", "suite_id": suite_id},
    ).json()["id"]
    execution = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": [case_id]},
    ).json()
    result_id = auth_client.get(f"/api/v1/executions/{execution['id']}/results").json()[0]["id"]
    return {"project_id": project_id, "execution_id": execution["id"], "result_id": result_id}


def _complete(auth_client, execution_id: int) -> None:
    auth_client.put(f"/api/v1/executions/{execution_id}", json={"status": "completed"})


def test_update_result_blocked_when_execution_completed(auth_client, execution_with_result):
    _complete(auth_client, execution_with_result["execution_id"])

    resp = auth_client.put(
        f"/api/v1/results/{execution_with_result['result_id']}",
        json={"status": "failed"},
    )

    assert resp.status_code == 409
    assert "read-only" in resp.json()["detail"]


def test_update_result_blocked_when_execution_aborted(auth_client, execution_with_result):
    auth_client.put(
        f"/api/v1/executions/{execution_with_result['execution_id']}",
        json={"status": "aborted"},
    )

    resp = auth_client.put(
        f"/api/v1/results/{execution_with_result['result_id']}",
        json={"status": "failed"},
    )

    assert resp.status_code == 409


def test_reopen_completed_execution_unlocks_updates(auth_client, execution_with_result):
    _complete(auth_client, execution_with_result["execution_id"])

    reopen = auth_client.post(f"/api/v1/executions/{execution_with_result['execution_id']}/reopen")

    assert reopen.status_code == 200
    body = reopen.json()
    assert body["status"] == "in_progress"
    assert body["finished_at"] is None

    follow_up = auth_client.put(
        f"/api/v1/results/{execution_with_result['result_id']}",
        json={"status": "failed"},
    )
    assert follow_up.status_code == 200


def test_reopen_rejects_when_execution_pending(auth_client, execution_with_result):
    resp = auth_client.post(f"/api/v1/executions/{execution_with_result['execution_id']}/reopen")

    assert resp.status_code == 409


def test_reopen_allowed_for_execution_creator_even_if_tester(client, auth_client, execution_with_result):
    with TestingSession() as db:
        db.add(User(
            username="tester", email="t@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        ))
        db.commit()
        tester_id = db.query(User).filter_by(username="tester").one().id
    auth_client.post(
        f"/api/v1/projects/{execution_with_result['project_id']}/members",
        json={"user_id": tester_id, "role": "tester"},
    )
    tester_token = client.post(
        "/api/v1/auth/login", data={"username": "tester", "password": "pw"},
    ).json()["access_token"]
    tester_execution_id = client.post(
        f"/api/v1/projects/{execution_with_result['project_id']}/executions",
        json={"title": "Tester-launched", "type": "manual", "test_case_ids": []},
        headers={"Authorization": f"Bearer {tester_token}"},
    ).json()["id"]
    client.put(
        f"/api/v1/executions/{tester_execution_id}",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {tester_token}"},
    )

    resp = client.post(
        f"/api/v1/executions/{tester_execution_id}/reopen",
        headers={"Authorization": f"Bearer {tester_token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_reopen_forbidden_for_non_creator_tester(client, auth_client, execution_with_result):
    _complete(auth_client, execution_with_result["execution_id"])
    with TestingSession() as db:
        db.add(User(
            username="bystander", email="b@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=False,
        ))
        db.commit()
        bystander_id = db.query(User).filter_by(username="bystander").one().id
    auth_client.post(
        f"/api/v1/projects/{execution_with_result['project_id']}/members",
        json={"user_id": bystander_id, "role": "tester"},
    )
    bystander_token = client.post(
        "/api/v1/auth/login", data={"username": "bystander", "password": "pw"},
    ).json()["access_token"]

    resp = client.post(
        f"/api/v1/executions/{execution_with_result['execution_id']}/reopen",
        headers={"Authorization": f"Bearer {bystander_token}"},
    )

    assert resp.status_code == 403
