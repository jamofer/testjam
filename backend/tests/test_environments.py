"""Tests for project environments catalog + auto-create from executions."""
import pytest


@pytest.fixture
def env_payload():
    return {
        "name": "Production EU",
        "slug": "production-eu",
        "description": "Live cluster eu-west-1",
        "host": "https://app.example.com",
        "color": "#10b981",
        "is_default": False,
    }


def _create_env(client, project_id, **overrides):
    payload = {"name": "Staging", "slug": "staging"}
    payload.update(overrides)
    return client.post(f"/api/v1/projects/{project_id}/environments", json=payload)


def test_create_environment(auth_client, project_id, env_payload):
    resp = _create_env(auth_client, project_id, **env_payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["slug"] == "production-eu"
    assert body["order"] == 1
    assert body["is_default"] is False
    assert body["archived_at"] is None


def test_list_environments_orders_by_order(auth_client, project_id):
    _create_env(auth_client, project_id, name="Dev", slug="dev")
    _create_env(auth_client, project_id, name="Prod", slug="prod")

    resp = auth_client.get(f"/api/v1/projects/{project_id}/environments")

    assert resp.status_code == 200
    slugs = [row["slug"] for row in resp.json()]
    assert slugs == ["dev", "prod"]


def test_unique_slug_per_project(auth_client, project_id):
    _create_env(auth_client, project_id, slug="prod")

    duplicate = _create_env(auth_client, project_id, slug="prod")

    assert duplicate.status_code == 409


def test_invalid_slug_rejected(auth_client, project_id):
    resp = _create_env(auth_client, project_id, slug="NotASlug")

    assert resp.status_code == 422


def test_setting_default_clears_previous_default(auth_client, project_id):
    first = _create_env(auth_client, project_id, slug="dev", is_default=True).json()
    second = _create_env(auth_client, project_id, slug="prod", is_default=True).json()

    listing = auth_client.get(f"/api/v1/projects/{project_id}/environments").json()
    by_slug = {row["slug"]: row for row in listing}

    assert by_slug["dev"]["is_default"] is False
    assert by_slug["prod"]["is_default"] is True
    assert first["id"] != second["id"]


def test_reorder_environments(auth_client, project_id):
    a = _create_env(auth_client, project_id, slug="a").json()
    b = _create_env(auth_client, project_id, slug="b").json()
    c = _create_env(auth_client, project_id, slug="c").json()

    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/environments/reorder",
        json={"ids": [c["id"], a["id"], b["id"]]},
    )

    assert resp.status_code == 200
    assert [row["slug"] for row in resp.json()] == ["c", "a", "b"]


def test_archive_then_unarchive(auth_client, project_id):
    env = _create_env(auth_client, project_id, slug="qa", is_default=True).json()

    archived = auth_client.post(f"/api/v1/environments/{env['id']}/archive").json()
    listing_default = auth_client.get(
        f"/api/v1/projects/{project_id}/environments",
    ).json()
    listing_full = auth_client.get(
        f"/api/v1/projects/{project_id}/environments?include_archived=true",
    ).json()
    unarchived = auth_client.post(f"/api/v1/environments/{env['id']}/unarchive").json()

    assert archived["archived_at"] is not None
    assert archived["is_default"] is False
    assert listing_default == []
    assert {row["slug"] for row in listing_full} == {"qa"}
    assert unarchived["archived_at"] is None


def test_delete_blocked_when_referenced_by_execution(auth_client, project_id):
    _create_env(auth_client, project_id, slug="prod")
    auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "environment": "prod", "test_case_ids": []},
    )
    env_id = auth_client.get(f"/api/v1/projects/{project_id}/environments").json()[0]["id"]

    resp = auth_client.delete(f"/api/v1/environments/{env_id}")

    assert resp.status_code == 409


def test_delete_allowed_when_unused(auth_client, project_id):
    env = _create_env(auth_client, project_id, slug="unused").json()

    resp = auth_client.delete(f"/api/v1/environments/{env['id']}")

    assert resp.status_code == 204
    listing = auth_client.get(f"/api/v1/projects/{project_id}/environments").json()
    assert listing == []


def test_execution_auto_creates_catalog_entry(auth_client, project_id):
    auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Run",
            "type": "manual",
            "environment": "Production EU",
            "test_case_ids": [],
        },
    )

    listing = auth_client.get(f"/api/v1/projects/{project_id}/environments").json()

    assert len(listing) == 1
    assert listing[0]["slug"] == "production-eu"
    assert listing[0]["name"] == "Production EU"


def test_execution_normalizes_environment_to_slug(auth_client, project_id):
    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Run",
            "type": "manual",
            "environment": "Staging Env",
            "test_case_ids": [],
        },
    )

    assert resp.json()["environment"] == "staging-env"


def test_execution_skips_auto_create_when_disabled(auth_client, project_id):
    auth_client.put(
        "/api/v1/settings",
        json={"auto_create_environments": False},
    )

    auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={
            "title": "Run",
            "type": "manual",
            "environment": "qa-cell",
            "test_case_ids": [],
        },
    )

    listing = auth_client.get(f"/api/v1/projects/{project_id}/environments").json()
    assert listing == []


def test_update_environment_name_and_color(auth_client, project_id):
    env = _create_env(auth_client, project_id, slug="prod").json()

    resp = auth_client.put(
        f"/api/v1/environments/{env['id']}",
        json={"name": "Renamed", "color": "#ff0000"},
    )

    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    assert resp.json()["color"] == "#ff0000"


def test_update_slug_blocked_when_referenced(auth_client, project_id):
    _create_env(auth_client, project_id, slug="prod")
    auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "environment": "prod", "test_case_ids": []},
    )
    env_id = auth_client.get(f"/api/v1/projects/{project_id}/environments").json()[0]["id"]

    resp = auth_client.put(
        f"/api/v1/environments/{env_id}",
        json={"slug": "renamed-prod"},
    )

    assert resp.status_code == 409
