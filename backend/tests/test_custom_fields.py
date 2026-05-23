import io

import openpyxl
import pytest


CUSTOM_FIELDS_PATH = "/api/v1/projects/{project_id}/custom-fields"


def _create_field(client, project_id, **overrides):
    payload = {
        "entity_type": "bug",
        "key": "priority",
        "label": "Priority",
        "type": "single_select",
        "options": [
            {"value": "p0", "label": "P0", "color": "#ef4444"},
            {"value": "p1", "label": "P1"},
        ],
    }
    payload.update(overrides)
    response = client.post(
        CUSTOM_FIELDS_PATH.format(project_id=project_id), json=payload
    )
    return response


def _create_bug(client, project_id, **overrides):
    payload = {"title": "Bug"}
    payload.update(overrides)
    return client.post(f"/api/v1/projects/{project_id}/bugs", json=payload)


def _bug_with_field(client, project_id, **overrides):
    response = _create_bug(client, project_id, **overrides)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def priority_field(auth_client, project_id):
    response = _create_field(auth_client, project_id)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_definition_assigns_position_and_defaults(auth_client, project_id):
    response = _create_field(auth_client, project_id, key="severity_score", type="number", options=None)

    assert response.status_code == 201
    body = response.json()
    assert body["position"] == 0
    assert body["required"] is False
    assert body["archived_at"] is None


def test_unique_key_per_entity_type(auth_client, project_id, priority_field):
    response = _create_field(auth_client, project_id)

    assert response.status_code == 409


def test_same_key_allowed_across_entity_types(auth_client, project_id, priority_field):
    response = _create_field(
        auth_client, project_id, entity_type="test_case"
    )

    assert response.status_code == 201


def test_select_requires_options(auth_client, project_id):
    response = _create_field(auth_client, project_id, options=None)

    assert response.status_code == 422


def test_non_select_rejects_options(auth_client, project_id):
    response = _create_field(
        auth_client,
        project_id,
        type="text",
        options=[{"value": "a", "label": "A"}],
        key="freeform",
    )

    assert response.status_code == 422


def test_execution_required_field_demands_default(auth_client, project_id):
    response = _create_field(
        auth_client,
        project_id,
        entity_type="execution",
        key="release_phase",
        type="single_select",
        options=[
            {"value": "alpha", "label": "Alpha"},
            {"value": "ga", "label": "GA"},
        ],
        required=True,
    )

    assert response.status_code == 422


def test_execution_required_with_default_accepted(auth_client, project_id):
    response = _create_field(
        auth_client,
        project_id,
        entity_type="execution",
        key="release_phase",
        type="single_select",
        options=[
            {"value": "alpha", "label": "Alpha"},
            {"value": "ga", "label": "GA"},
        ],
        required=True,
        default_value="alpha",
    )

    assert response.status_code == 201


def test_test_case_required_field_demands_default(auth_client, project_id):
    response = _create_field(
        auth_client,
        project_id,
        entity_type="test_case",
        key="component",
        type="single_select",
        options=[
            {"value": "ui", "label": "UI"},
            {"value": "api", "label": "API"},
        ],
        required=True,
    )

    assert response.status_code == 422


def test_test_case_required_with_default_accepted(auth_client, project_id):
    response = _create_field(
        auth_client,
        project_id,
        entity_type="test_case",
        key="component",
        type="single_select",
        options=[
            {"value": "ui", "label": "UI"},
            {"value": "api", "label": "API"},
        ],
        required=True,
        default_value="ui",
    )

    assert response.status_code == 201


def test_test_case_required_default_autofills_on_inline_create(auth_client, project_id):
    _create_field(
        auth_client,
        project_id,
        entity_type="test_case",
        key="component",
        type="single_select",
        options=[
            {"value": "ui", "label": "UI"},
            {"value": "api", "label": "API"},
        ],
        required=True,
        default_value="ui",
    )

    suite = auth_client.post(
        f"/api/v1/projects/{project_id}/suites",
        json={"name": "Suite"},
    ).json()
    response = auth_client.post(
        f"/api/v1/suites/{suite['id']}/cases",
        json={"name": "Case", "suite_id": suite["id"]},
    )

    assert response.status_code == 201
    assert response.json()["custom_fields"] == {"component": "ui"}


def test_default_value_must_match_options(auth_client, project_id):
    response = _create_field(
        auth_client,
        project_id,
        default_value="ghost",
    )

    assert response.status_code == 422


def test_bug_create_accepts_valid_value(auth_client, project_id, priority_field):
    bug = _bug_with_field(
        auth_client, project_id, custom_fields={"priority": "p0"}
    )

    assert bug["custom_fields"] == {"priority": "p0"}


def test_bug_create_rejects_unknown_option(auth_client, project_id, priority_field):
    response = _create_bug(
        auth_client, project_id, custom_fields={"priority": "ghost"}
    )

    assert response.status_code == 422


def test_bug_create_discards_unknown_keys(auth_client, project_id, priority_field):
    bug = _bug_with_field(
        auth_client,
        project_id,
        custom_fields={"priority": "p0", "phantom": "value"},
    )

    assert bug["custom_fields"] == {"priority": "p0"}


def test_required_field_blocks_create_without_value(auth_client, project_id):
    _create_field(
        auth_client,
        project_id,
        key="customer_impact",
        type="bool",
        options=None,
        required=True,
    )

    response = _create_bug(auth_client, project_id)

    assert response.status_code == 422


def test_required_field_with_default_auto_fills(auth_client, project_id):
    _create_field(
        auth_client,
        project_id,
        key="customer_impact",
        type="bool",
        options=None,
        required=True,
        default_value=False,
    )

    bug = _bug_with_field(auth_client, project_id)

    assert bug["custom_fields"] == {"customer_impact": False}


def test_bug_update_can_clear_value(auth_client, project_id, priority_field):
    bug = _bug_with_field(
        auth_client, project_id, custom_fields={"priority": "p0"}
    )

    response = auth_client.put(
        f"/api/v1/bugs/{bug['id']}",
        json={"custom_fields": {"priority": None}},
    )

    assert response.status_code == 200
    assert response.json()["custom_fields"] == {}


def test_bug_update_merges_into_existing_values(auth_client, project_id, priority_field):
    _create_field(
        auth_client,
        project_id,
        key="customer_impact",
        type="bool",
        options=None,
    )
    bug = _bug_with_field(
        auth_client,
        project_id,
        custom_fields={"priority": "p0", "customer_impact": True},
    )

    response = auth_client.put(
        f"/api/v1/bugs/{bug['id']}",
        json={"custom_fields": {"priority": "p1"}},
    )

    assert response.status_code == 200
    assert response.json()["custom_fields"] == {"priority": "p1", "customer_impact": True}


def test_type_validation_per_type(auth_client, project_id):
    _create_field(
        auth_client, project_id, key="ratio", type="number", options=None
    )

    response = _create_bug(
        auth_client, project_id, custom_fields={"ratio": "not a number"}
    )

    assert response.status_code == 422


def test_multi_select_accepts_list(auth_client, project_id):
    _create_field(
        auth_client,
        project_id,
        key="platforms",
        type="multi_select",
        options=[
            {"value": "web", "label": "Web"},
            {"value": "ios", "label": "iOS"},
        ],
    )

    bug = _bug_with_field(
        auth_client, project_id, custom_fields={"platforms": ["web", "ios"]}
    )

    assert bug["custom_fields"]["platforms"] == ["web", "ios"]


def test_multi_select_rejects_unknown_option(auth_client, project_id):
    _create_field(
        auth_client,
        project_id,
        key="platforms",
        type="multi_select",
        options=[{"value": "web", "label": "Web"}],
    )

    response = _create_bug(
        auth_client, project_id, custom_fields={"platforms": ["ghost"]}
    )

    assert response.status_code == 422


def test_filter_bugs_by_custom_field(auth_client, project_id, priority_field):
    _bug_with_field(auth_client, project_id, custom_fields={"priority": "p0"})
    _bug_with_field(auth_client, project_id, custom_fields={"priority": "p1"})
    _bug_with_field(auth_client, project_id)

    response = auth_client.get(
        f"/api/v1/projects/{project_id}/bugs?cf_key=priority&cf_value=p0"
    )

    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 1
    assert matches[0]["custom_fields"]["priority"] == "p0"


def test_filter_bugs_by_bool_custom_field(auth_client, project_id):
    _create_field(
        auth_client, project_id, key="regression", type="bool", options=None,
    )
    _bug_with_field(auth_client, project_id, custom_fields={"regression": True})
    _bug_with_field(auth_client, project_id, custom_fields={"regression": False})

    true_response = auth_client.get(
        f"/api/v1/projects/{project_id}/bugs?cf_key=regression&cf_value=true"
    )
    false_response = auth_client.get(
        f"/api/v1/projects/{project_id}/bugs?cf_key=regression&cf_value=false"
    )

    assert true_response.status_code == 200
    assert false_response.status_code == 200
    true_matches = true_response.json()
    false_matches = false_response.json()
    assert len(true_matches) == 1
    assert true_matches[0]["custom_fields"]["regression"] is True
    assert len(false_matches) == 1
    assert false_matches[0]["custom_fields"]["regression"] is False


def test_delete_blocked_when_values_exist(auth_client, project_id, priority_field):
    _bug_with_field(auth_client, project_id, custom_fields={"priority": "p0"})

    response = auth_client.delete(f"/api/v1/custom-fields/{priority_field['id']}")

    assert response.status_code == 409


def test_archive_keeps_orphan_values(auth_client, project_id, priority_field):
    bug = _bug_with_field(
        auth_client, project_id, custom_fields={"priority": "p0"}
    )
    auth_client.post(f"/api/v1/custom-fields/{priority_field['id']}/archive")

    response = auth_client.get(f"/api/v1/bugs/{bug['id']}")

    assert response.status_code == 200
    assert response.json()["custom_fields"] == {"priority": "p0"}


def test_reorder_rewrites_positions(auth_client, project_id):
    first = _create_field(auth_client, project_id, key="a", type="text", options=None).json()
    second = _create_field(auth_client, project_id, key="b", type="text", options=None).json()
    third = _create_field(auth_client, project_id, key="c", type="text", options=None).json()

    response = auth_client.post(
        CUSTOM_FIELDS_PATH.format(project_id=project_id) + "/reorder",
        json={"ids": [third["id"], first["id"], second["id"]]},
    )

    assert response.status_code == 200
    ordered = response.json()
    assert [field["key"] for field in ordered] == ["c", "a", "b"]


def test_reorder_rejects_mixed_entity_types(auth_client, project_id, priority_field):
    case_field = _create_field(
        auth_client, project_id, entity_type="test_case", key="prio_case"
    ).json()

    response = auth_client.post(
        CUSTOM_FIELDS_PATH.format(project_id=project_id) + "/reorder",
        json={"ids": [priority_field["id"], case_field["id"]]},
    )

    assert response.status_code == 400


def test_xlsx_report_appends_custom_field_columns(auth_client, project_id, priority_field):
    _create_field(
        auth_client,
        project_id,
        key="env_type",
        label="Env type",
        type="multi_select",
        options=[
            {"value": "browser", "label": "Browser"},
            {"value": "mobile", "label": "Mobile"},
        ],
    )
    _bug_with_field(
        auth_client,
        project_id,
        custom_fields={"priority": "p0", "env_type": ["browser", "mobile"]},
    )

    response = auth_client.get(
        f"/api/v1/projects/{project_id}/bugs/report?format=xlsx"
    )

    workbook = openpyxl.load_workbook(io.BytesIO(response.content))
    rows = list(workbook["Bugs"].iter_rows(values_only=True))
    header = rows[0]
    assert header[-2:] == ("Priority", "Env type")
    body = rows[1]
    assert body[-2:] == ("P0", "Browser, Mobile")


def test_html_report_renders_custom_field_chips(auth_client, project_id, priority_field):
    _bug_with_field(
        auth_client, project_id, custom_fields={"priority": "p0"},
    )

    response = auth_client.get(
        f"/api/v1/projects/{project_id}/bugs/report?format=html"
    )

    body = response.text
    assert "cf-chip" in body
    assert "Priority:" in body
    assert "P0</span>" in body
    assert "background:#ef4444" in body


def test_test_case_accepts_custom_fields(auth_client, project_id, suite_id):
    _create_field(
        auth_client,
        project_id,
        entity_type="test_case",
        key="test_type",
        type="single_select",
        options=[
            {"value": "smoke", "label": "Smoke"},
            {"value": "regression", "label": "Regression"},
        ],
    )

    response = auth_client.post(
        f"/api/v1/suites/{suite_id}/cases",
        json={
            "name": "TC",
            "suite_id": suite_id,
            "custom_fields": {"test_type": "smoke"},
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["custom_fields"] == {"test_type": "smoke"}


def test_execution_default_value_applied_on_create(auth_client, project_id):
    _create_field(
        auth_client,
        project_id,
        entity_type="execution",
        key="release_phase",
        type="single_select",
        options=[
            {"value": "alpha", "label": "Alpha"},
            {"value": "ga", "label": "GA"},
        ],
        required=True,
        default_value="alpha",
    )

    response = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["custom_fields"] == {"release_phase": "alpha"}


def test_archive_then_unarchive_round_trip(auth_client, priority_field):
    auth_client.post(f"/api/v1/custom-fields/{priority_field['id']}/archive")

    response = auth_client.post(
        f"/api/v1/custom-fields/{priority_field['id']}/unarchive"
    )

    assert response.status_code == 200
    assert response.json()["archived_at"] is None
