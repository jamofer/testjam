import pytest

ORIGINAL_DESCRIPTION = "Steps: open the page"


@pytest.fixture
def bug_id(auth_client, project_id):
    return auth_client.post(
        f"/api/v1/projects/{project_id}/bugs",
        json={"title": "Crash on save", "description": ORIGINAL_DESCRIPTION},
    ).json()["id"]


def test_edit_from_current_value_is_saved(auth_client, bug_id):
    response = auth_client.put(
        f"/api/v1/bugs/{bug_id}",
        json={"description": "Steps: open and save", "previous_values": {"description": ORIGINAL_DESCRIPTION}},
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Steps: open and save"


def test_edit_from_stale_value_is_rejected(auth_client, bug_id):
    auth_client.put(f"/api/v1/bugs/{bug_id}", json={"description": "Rewritten by a teammate"})

    response = auth_client.put(
        f"/api/v1/bugs/{bug_id}",
        json={"description": "My version", "previous_values": {"description": ORIGINAL_DESCRIPTION}},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["field"] == "description"
    assert response.json()["detail"]["current"] == "Rewritten by a teammate"
    assert auth_client.get(f"/api/v1/bugs/{bug_id}").json()["description"] == "Rewritten by a teammate"


def test_changes_to_other_fields_do_not_conflict(auth_client, bug_id):
    auth_client.put(f"/api/v1/bugs/{bug_id}", json={"severity": "high"})
    auth_client.post(f"/api/v1/bugs/{bug_id}/comments", json={"body": "Seen on staging"})

    response = auth_client.put(
        f"/api/v1/bugs/{bug_id}",
        json={"title": "Crash on first save", "previous_values": {"title": "Crash on save"}},
    )

    assert response.status_code == 200


def test_edit_without_previous_values_keeps_last_write_wins(auth_client, bug_id):
    auth_client.put(f"/api/v1/bugs/{bug_id}", json={"title": "Teammate title"})

    response = auth_client.put(f"/api/v1/bugs/{bug_id}", json={"title": "My title"})

    assert response.json()["title"] == "My title"


def test_previous_values_only_accept_text_fields(auth_client, bug_id):
    response = auth_client.put(
        f"/api/v1/bugs/{bug_id}",
        json={"severity": "low", "previous_values": {"severity": "medium"}},
    )

    assert response.status_code == 422
