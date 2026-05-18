"""F0 scaffold tests: CRUD + push/sync against the in-process fake provider."""
import pytest

from testjam.services.integrations.providers.fake import instance as fake_provider


@pytest.fixture(autouse=True)
def reset_fake_provider():
    fake_provider().reset()
    yield
    fake_provider().reset()


@pytest.fixture
def integration_payload():
    return {
        "provider": "fake",
        "name": "Primary",
        "config": {"project_key": "DEMO"},
        "status_mapping": {"Done": "closed"},
        "is_active": True,
        "secret": "supersecret",
    }


def test_create_integration_returns_redacted_payload(
    auth_client, project_id, integration_payload,
):
    resp = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["provider"] == "fake"
    assert body["name"] == "Primary"
    assert body["has_credential"] is True
    assert "secret" not in body
    assert "secret_encrypted" not in body


def test_create_integration_rejects_invalid_config(auth_client, project_id):
    bad = {"provider": "fake", "name": "Broken", "config": {}, "secret": "x"}

    resp = auth_client.post(f"/api/v1/projects/{project_id}/integrations", json=bad)

    assert resp.status_code == 400
    assert "project_key" in resp.json()["detail"]


def test_list_integrations(auth_client, project_id, integration_payload):
    auth_client.post(f"/api/v1/projects/{project_id}/integrations", json=integration_payload)

    resp = auth_client.get(f"/api/v1/projects/{project_id}/integrations")

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["provider"] == "fake"


def test_update_integration_name_and_active_flag(auth_client, project_id, integration_payload):
    integration_id = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    ).json()["id"]

    resp = auth_client.put(
        f"/api/v1/integrations/{integration_id}",
        json={"name": "Renamed", "is_active": False},
    )

    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    assert resp.json()["is_active"] is False


def test_rotate_credential_keeps_integration(auth_client, project_id, integration_payload):
    integration_id = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    ).json()["id"]

    resp = auth_client.post(
        f"/api/v1/integrations/{integration_id}/rotate-credential",
        json={"secret": "fresh"},
    )

    assert resp.status_code == 200
    assert resp.json()["has_credential"] is True


def test_health_check_passes_for_valid_integration(auth_client, project_id, integration_payload):
    integration_id = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    ).json()["id"]

    resp = auth_client.post(f"/api/v1/integrations/{integration_id}/test")

    assert resp.status_code == 204


def test_push_creates_external_link(auth_client, project_id, integration_payload):
    integration_id = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    ).json()["id"]
    bug = auth_client.post(
        f"/api/v1/projects/{project_id}/bugs",
        json={"title": "Crash on login", "description": "Steps…"},
    ).json()

    resp = auth_client.post(
        f"/api/v1/bugs/{bug['id']}/external-links",
        json={"integration_id": integration_id},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["provider"] == "fake"
    assert body["external_id"].startswith("DEMO-")
    assert body["url"].startswith("https://fake.example/tickets/DEMO-")
    assert body["status_normalized"] == "open"


def test_sync_link_reflects_remote_status_change(auth_client, project_id, integration_payload):
    integration_id = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    ).json()["id"]
    bug = auth_client.post(
        f"/api/v1/projects/{project_id}/bugs", json={"title": "Crash"},
    ).json()
    link = auth_client.post(
        f"/api/v1/bugs/{bug['id']}/external-links",
        json={"integration_id": integration_id},
    ).json()
    fake_provider().set_remote_status(link["external_id"], "Done")

    resp = auth_client.post(
        f"/api/v1/bugs/{bug['id']}/external-links/{link['id']}/sync",
    )

    assert resp.status_code == 200
    assert resp.json()["status_raw"] == "Done"
    assert resp.json()["status_normalized"] == "closed"


def test_push_rejected_for_disabled_integration(auth_client, project_id, integration_payload):
    integration_id = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    ).json()["id"]
    auth_client.put(f"/api/v1/integrations/{integration_id}", json={"is_active": False})
    bug = auth_client.post(
        f"/api/v1/projects/{project_id}/bugs", json={"title": "Crash"},
    ).json()

    resp = auth_client.post(
        f"/api/v1/bugs/{bug['id']}/external-links",
        json={"integration_id": integration_id},
    )

    assert resp.status_code == 400


def test_delete_integration_cascades_links(auth_client, project_id, integration_payload):
    integration_id = auth_client.post(
        f"/api/v1/projects/{project_id}/integrations", json=integration_payload,
    ).json()["id"]
    bug = auth_client.post(
        f"/api/v1/projects/{project_id}/bugs", json={"title": "Crash"},
    ).json()
    auth_client.post(
        f"/api/v1/bugs/{bug['id']}/external-links",
        json={"integration_id": integration_id},
    )

    assert auth_client.delete(f"/api/v1/integrations/{integration_id}").status_code == 204
    links = auth_client.get(f"/api/v1/bugs/{bug['id']}/external-links").json()
    assert all(link["integration_id"] is None for link in links)


def test_providers_listing_includes_fake(auth_client):
    resp = auth_client.get("/api/v1/integrations/providers")

    assert resp.status_code == 200
    keys = {row["key"] for row in resp.json()}
    assert "fake" in keys