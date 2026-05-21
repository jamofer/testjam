"""Custom field definition + value pass-through SDK coverage."""


def _create_project(auth_client):
    return auth_client.projects.find_or_create("CFProj")


def _create_priority_field(auth_client, project_id):
    return auth_client.custom_fields.create(
        project_id,
        entity_type="bug",
        key="priority",
        label="Priority",
        type="single_select",
        options=[
            {"value": "p0", "label": "P0", "color": "#ef4444"},
            {"value": "p1", "label": "P1"},
        ],
    )


def test_create_and_list_definitions(auth_client):
    project = _create_project(auth_client)
    field = _create_priority_field(auth_client, project["id"])

    listing = auth_client.custom_fields.list(project["id"], "bug")

    assert [definition["id"] for definition in listing] == [field["id"]]
    assert field["type"] == "single_select"


def test_update_label(auth_client):
    project = _create_project(auth_client)
    field = _create_priority_field(auth_client, project["id"])

    updated = auth_client.custom_fields.update(field["id"], label="Urgency")

    assert updated["label"] == "Urgency"


def test_archive_and_unarchive_round_trip(auth_client):
    project = _create_project(auth_client)
    field = _create_priority_field(auth_client, project["id"])

    archived = auth_client.custom_fields.archive(field["id"])
    restored = auth_client.custom_fields.unarchive(field["id"])

    assert archived["archived_at"] is not None
    assert restored["archived_at"] is None


def test_reorder_rewrites_positions(auth_client):
    project = _create_project(auth_client)
    text_a = auth_client.custom_fields.create(
        project["id"], entity_type="bug", key="alpha", label="A", type="text",
    )
    text_b = auth_client.custom_fields.create(
        project["id"], entity_type="bug", key="bravo", label="B", type="text",
    )

    reordered = auth_client.custom_fields.reorder(project["id"], [text_b["id"], text_a["id"]])

    assert [definition["key"] for definition in reordered] == ["bravo", "alpha"]


def test_bug_create_accepts_custom_fields(auth_client):
    project = _create_project(auth_client)
    _create_priority_field(auth_client, project["id"])

    bug = auth_client.bugs.create(
        project["id"],
        title="Crash",
        custom_fields={"priority": "p0"},
    )

    assert bug["custom_fields"] == {"priority": "p0"}


def test_bug_list_filters_by_custom_field(auth_client):
    project = _create_project(auth_client)
    _create_priority_field(auth_client, project["id"])
    auth_client.bugs.create(project["id"], title="A", custom_fields={"priority": "p0"})
    auth_client.bugs.create(project["id"], title="B", custom_fields={"priority": "p1"})

    matches = auth_client.bugs.list(project["id"], cf_key="priority", cf_value="p0")

    assert {bug["custom_fields"]["priority"] for bug in matches} == {"p0"}


def test_case_create_accepts_custom_fields(auth_client):
    project = _create_project(auth_client)
    suite = auth_client.suites.create(project["id"], name="Smoke")
    auth_client.custom_fields.create(
        project["id"],
        entity_type="test_case",
        key="test_type",
        label="Type",
        type="single_select",
        options=[{"value": "smoke", "label": "Smoke"}],
    )

    case = auth_client.cases.create(
        suite["id"], name="TC", custom_fields={"test_type": "smoke"},
    )

    assert case["custom_fields"] == {"test_type": "smoke"}


def test_execution_default_value_auto_applied(auth_client):
    project = _create_project(auth_client)
    auth_client.custom_fields.create(
        project["id"],
        entity_type="execution",
        key="release_phase",
        label="Phase",
        type="single_select",
        options=[
            {"value": "alpha", "label": "Alpha"},
            {"value": "ga", "label": "GA"},
        ],
        required=True,
        default_value="alpha",
    )

    execution = auth_client.executions.create(project["id"], title="Run", type="manual")

    assert execution["custom_fields"] == {"release_phase": "alpha"}
