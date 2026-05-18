"""Azure DevOps provider tests with httpx MockTransport."""
import base64
import json

import httpx
import pytest

from testjam.services.integrations.base import (
    ProviderConfigError,
    ProviderRequestError,
)
from testjam.services.integrations.providers.azure_devops import AzureDevOpsProvider


ORG = "https://dev.azure.com/acme"
PROJECT_ENCODED = "Widgets%20Co"


@pytest.fixture
def provider():
    return AzureDevOpsProvider()


@pytest.fixture
def config(provider):
    return provider.validate_config({
        "organization_url": ORG, "project": "Widgets Co", "work_item_type": "Bug",
    })


def _install(monkeypatch, handler):
    transport = httpx.MockTransport(handler)

    class StubClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(
        "testjam.services.integrations.providers.azure_devops.httpx.Client", StubClient,
    )


def test_validate_config_requires_organization_url(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({"project": "P"})


def test_validate_config_requires_project(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({"organization_url": ORG})


def test_validate_config_defaults_work_item_type(provider):
    result = provider.validate_config({"organization_url": ORG, "project": "P"})

    assert result["work_item_type"] == "Bug"


def test_health_check_sends_basic_token(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"count": 1, "value": []})

    _install(monkeypatch, handler)

    provider.health_check(config, "pat_abc")

    assert captured["url"] == (
        f"{ORG}/{PROJECT_ENCODED}/_apis/wit/workitemtypes?api-version=7.1"
    )
    expected_token = base64.b64encode(b":pat_abc").decode()
    assert captured["auth"] == f"Basic {expected_token}"


def test_health_check_raises_on_401(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(401))

    with pytest.raises(ProviderConfigError):
        provider.health_check(config, "tok")


def test_create_ticket_posts_json_patch(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers.get("content-type")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={
            "id": 123,
            "fields": {"System.State": "New"},
            "_links": {"html": {"href": f"{ORG}/Widgets%20Co/_workitems/edit/123"}},
        })

    _install(monkeypatch, handler)

    ticket = provider.create_ticket(
        config, "tok",
        title="Crash", body_markdown="Steps with **bold**", labels=["smoke", "p1"],
    )

    assert captured["url"] == (
        f"{ORG}/{PROJECT_ENCODED}/_apis/wit/workitems/$Bug?api-version=7.1"
    )
    assert captured["content_type"] == "application/json-patch+json"
    ops = captured["body"]
    assert ops[0] == {"op": "add", "path": "/fields/System.Title", "value": "Crash"}
    assert ops[1]["path"] == "/fields/System.Description"
    assert "<strong>bold</strong>" in ops[1]["value"]
    assert ops[2] == {"op": "add", "path": "/fields/System.Tags", "value": "smoke; p1"}
    assert ticket.external_id == "123"
    assert ticket.url == f"{ORG}/Widgets%20Co/_workitems/edit/123"
    assert ticket.status_normalized == "open"


def test_create_ticket_surfaces_api_error(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(400, text="bad patch"))

    with pytest.raises(ProviderRequestError):
        provider.create_ticket(config, "tok", title="x", body_markdown="")


def test_fetch_status_done_maps_to_closed(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "fields": {"System.State": "Done"},
    }))

    ticket = provider.fetch_status(config, "tok", "9")

    assert ticket.status_raw == "Done"
    assert ticket.status_normalized == "closed"


def test_fetch_status_unknown_state_treated_as_open(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "fields": {"System.State": "In Review"},
    }))

    ticket = provider.fetch_status(config, "tok", "9")

    assert ticket.status_normalized == "open"


def test_fetch_status_unknown_when_404(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(404))

    ticket = provider.fetch_status(config, "tok", "999")

    assert ticket.status_normalized == "unknown"


def test_normalize_status_honors_custom_mapping(provider):
    assert provider.normalize_status("Triage", {"Triage": "open"}) == "open"
    assert provider.normalize_status("Removed", {}) == "closed"
