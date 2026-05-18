"""JiraProvider tests with httpx MockTransport."""
import base64
import json

import httpx
import pytest

from testjam.services.integrations.base import (
    ProviderConfigError,
    ProviderRequestError,
)
from testjam.services.integrations.providers.jira import JiraProvider


BASE = "https://acme.atlassian.net"


@pytest.fixture
def provider():
    return JiraProvider()


@pytest.fixture
def config(provider):
    return provider.validate_config({
        "base_url": BASE, "project_key": "TJ", "email": "alice@example.org",
    })


def _install(monkeypatch, handler):
    transport = httpx.MockTransport(handler)

    class StubClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(
        "testjam.services.integrations.providers.jira.httpx.Client", StubClient,
    )


def test_validate_config_normalizes_base_url(provider):
    result = provider.validate_config({
        "base_url": f"{BASE}/", "project_key": "TJ",
    })

    assert result["base_url"] == BASE
    assert result["issue_type"] == "Bug"


def test_validate_config_requires_project_key(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({"base_url": BASE})


def test_health_check_uses_basic_auth(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"key": "TJ"})

    _install(monkeypatch, handler)

    provider.health_check(config, "tok_abc")

    assert captured["url"] == f"{BASE}/rest/api/3/project/TJ"
    expected_token = base64.b64encode(b"alice@example.org:tok_abc").decode()
    assert captured["auth"] == f"Basic {expected_token}"


def test_health_check_uses_bearer_when_no_email(monkeypatch, provider):
    config = provider.validate_config({"base_url": BASE, "project_key": "TJ"})
    captured = {}

    def handler(request):
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"key": "TJ"})

    _install(monkeypatch, handler)

    provider.health_check(config, "pat_token")

    assert captured["auth"] == "Bearer pat_token"


def test_create_ticket_posts_adf_body(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"key": "TJ-7", "id": "10001"})

    _install(monkeypatch, handler)

    ticket = provider.create_ticket(
        config, "tok",
        title="Login crash", body_markdown="**bold** steps", labels=["smoke test"],
    )

    body = captured["body"]
    assert body["fields"]["project"] == {"key": "TJ"}
    assert body["fields"]["summary"] == "Login crash"
    assert body["fields"]["issuetype"] == {"name": "Bug"}
    assert body["fields"]["labels"] == ["smoke-test"]  # spaces stripped
    description = body["fields"]["description"]
    assert description["type"] == "doc"
    assert description["content"][0]["content"][0]["marks"] == [{"type": "strong"}]
    assert ticket.external_id == "TJ-7"
    assert ticket.url == f"{BASE}/browse/TJ-7"


def test_create_ticket_surfaces_api_error(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(400, text="invalid project"))

    with pytest.raises(ProviderRequestError):
        provider.create_ticket(config, "tok", title="x", body_markdown="")


def test_fetch_status_done_maps_to_closed(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "fields": {"status": {"name": "Done"}},
    }))

    ticket = provider.fetch_status(config, "tok", "TJ-5")

    assert ticket.status_raw == "Done"
    assert ticket.status_normalized == "closed"


def test_fetch_status_in_progress_maps_to_open(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "fields": {"status": {"name": "In Progress"}},
    }))

    ticket = provider.fetch_status(config, "tok", "TJ-5")

    assert ticket.status_normalized == "open"


def test_fetch_status_unknown_when_404(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(404))

    ticket = provider.fetch_status(config, "tok", "TJ-99")

    assert ticket.status_normalized == "unknown"


def test_normalize_status_honors_custom_mapping(provider):
    assert provider.normalize_status("Triage", {"Triage": "open"}) == "open"
    assert provider.normalize_status("Wont Do", {"Wont Do": "closed"}) == "closed"
