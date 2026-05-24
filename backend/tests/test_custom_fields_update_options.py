"""Option-edit guards on ``PUT /custom-fields/{id}``.

Admins occasionally curate option lists after a select field is live.
Two failure modes are silent without these guards:

* Removing an option that is still stored on existing rows leaves those
  values as ghosts — the form can't re-select them and a follow-up PUT
  that omits ``custom_fields`` strips them entirely.
* Replacing the option set without revisiting ``default_value`` makes
  future creates explode with a 422 the user can't act on (the default
  applies, then validation rejects it).

These tests pin both behaviours so a regression is caught immediately.
"""
import pytest

CUSTOM_FIELDS_PATH = "/api/v1/projects/{project_id}/custom-fields"


def _create_priority(client, project_id, **overrides):
    payload = {
        "entity_type": "bug",
        "key": "priority",
        "label": "Priority",
        "type": "single_select",
        "options": [
            {"value": "p0", "label": "P0"},
            {"value": "p1", "label": "P1"},
            {"value": "p2", "label": "P2"},
        ],
    }
    payload.update(overrides)
    response = client.post(
        CUSTOM_FIELDS_PATH.format(project_id=project_id), json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_components(client, project_id):
    return _create_priority(
        client, project_id,
        key="components", label="Components", type="multi_select",
        options=[
            {"value": "api", "label": "API"},
            {"value": "ui", "label": "UI"},
            {"value": "docs", "label": "Docs"},
        ],
    )


def _create_bug(client, project_id, custom_fields=None):
    body = {"title": "Bug"}
    if custom_fields is not None:
        body["custom_fields"] = custom_fields
    response = client.post(f"/api/v1/projects/{project_id}/bugs", json=body)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def priority_field(auth_client, project_id):
    return _create_priority(auth_client, project_id)


@pytest.fixture
def components_field(auth_client, project_id):
    return _create_components(auth_client, project_id)


def test_removing_unused_option_is_allowed(auth_client, project_id, priority_field):
    response = auth_client.put(
        f"/api/v1/custom-fields/{priority_field['id']}",
        json={"options": [
            {"value": "p0", "label": "P0"},
            {"value": "p1", "label": "P1"},
        ]},
    )

    assert response.status_code == 200, response.text
    assert {opt["value"] for opt in response.json()["options"]} == {"p0", "p1"}


def test_removing_option_referenced_by_a_bug_is_refused(auth_client, project_id, priority_field):
    _create_bug(auth_client, project_id, custom_fields={"priority": "p2"})

    response = auth_client.put(
        f"/api/v1/custom-fields/{priority_field['id']}",
        json={"options": [
            {"value": "p0", "label": "P0"},
            {"value": "p1", "label": "P1"},
        ]},
    )

    assert response.status_code == 409
    assert "p2" in response.json()["detail"]


def test_removing_multi_select_option_referenced_by_a_bug_is_refused(
    auth_client, project_id, components_field,
):
    _create_bug(auth_client, project_id, custom_fields={"components": ["api", "docs"]})

    response = auth_client.put(
        f"/api/v1/custom-fields/{components_field['id']}",
        json={"options": [
            {"value": "api", "label": "API"},
            {"value": "ui", "label": "UI"},
        ]},
    )

    assert response.status_code == 409
    assert "docs" in response.json()["detail"]


def test_replacing_options_invalidates_existing_default(auth_client, project_id):
    field = _create_priority(auth_client, project_id, default_value="p0")

    response = auth_client.put(
        f"/api/v1/custom-fields/{field['id']}",
        json={"options": [
            {"value": "p1", "label": "P1"},
            {"value": "p2", "label": "P2"},
        ]},
    )

    assert response.status_code == 422
    assert "p0" in response.json()["detail"]


def test_replacing_options_and_default_together_is_accepted(auth_client, project_id):
    field = _create_priority(auth_client, project_id, default_value="p0")

    response = auth_client.put(
        f"/api/v1/custom-fields/{field['id']}",
        json={
            "options": [
                {"value": "p1", "label": "P1"},
                {"value": "p2", "label": "P2"},
            ],
            "default_value": "p1",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["default_value"] == "p1"


def test_clearing_default_alongside_options_change_is_accepted(auth_client, project_id):
    field = _create_priority(auth_client, project_id, default_value="p0")

    response = auth_client.put(
        f"/api/v1/custom-fields/{field['id']}",
        json={
            "options": [
                {"value": "p1", "label": "P1"},
                {"value": "p2", "label": "P2"},
            ],
            "default_value": None,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["default_value"] is None


def test_multi_select_default_revalidated_against_new_options(auth_client, project_id):
    field = _create_components(auth_client, project_id)
    auth_client.put(
        f"/api/v1/custom-fields/{field['id']}",
        json={"default_value": ["api", "ui"]},
    )

    response = auth_client.put(
        f"/api/v1/custom-fields/{field['id']}",
        json={"options": [
            {"value": "api", "label": "API"},
            {"value": "docs", "label": "Docs"},
        ]},
    )

    assert response.status_code == 422
    assert "ui" in response.json()["detail"]
