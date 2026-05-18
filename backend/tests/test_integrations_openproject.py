"""OpenProjectProvider tests with httpx MockTransport."""
import base64
import json

import httpx
import pytest

from testjam.services.integrations.base import (
    ProviderConfigError,
    ProviderRequestError,
)
from testjam.services.integrations.providers.openproject import OpenProjectProvider


BASE = "https://openproject.example.org"
PROJECT_ID = "tj"


@pytest.fixture
def provider():
    return OpenProjectProvider()


@pytest.fixture
def config(provider):
    return provider.validate_config({
        "base_url": BASE, "project": PROJECT_ID, "type_id": 1,
    })


def _install(monkeypatch, handler):
    transport = httpx.MockTransport(handler)

    class StubClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(
        "testjam.services.integrations.providers.openproject.httpx.Client", StubClient,
    )


def test_validate_config_requires_base_url(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({"project": "x"})


def test_validate_config_requires_project(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({"base_url": BASE})


def test_validate_config_rejects_non_numeric_type_id(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({"base_url": BASE, "project": "tj", "type_id": "Bug"})


def test_validate_config_omits_type_when_empty(provider):
    out = provider.validate_config({"base_url": f"{BASE}/", "project": "tj", "type_id": ""})

    assert out == {"base_url": BASE, "project": "tj"}


def test_health_check_uses_apikey_basic(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"id": 1})

    _install(monkeypatch, handler)

    provider.health_check(config, "tok_abc")

    assert captured["url"] == f"{BASE}/api/v3/projects/{PROJECT_ID}"
    expected_token = base64.b64encode(b"apikey:tok_abc").decode()
    assert captured["auth"] == f"Basic {expected_token}"


def test_health_check_raises_on_401(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(401))

    with pytest.raises(ProviderConfigError):
        provider.health_check(config, "tok")


def test_create_work_package_posts_body_with_type_link(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={
            "id": 42,
            "_links": {"self": {"href": f"/api/v3/work_packages/42"}, "status": {"title": "New"}},
        })

    _install(monkeypatch, handler)

    ticket = provider.create_ticket(
        config, "tok",
        title="Crash", body_markdown="**bold** steps", labels=None,
    )

    assert captured["url"] == f"{BASE}/api/v3/projects/{PROJECT_ID}/work_packages"
    body = captured["body"]
    assert body["subject"] == "Crash"
    assert body["description"] == {"raw": "**bold** steps"}
    assert body["_links"] == {"type": {"href": "/api/v3/types/1"}}
    assert ticket.external_id == "42"
    assert ticket.url == f"{BASE}/api/v3/work_packages/42"
    assert ticket.status_raw == "New"
    assert ticket.status_normalized == "open"


def test_create_work_package_without_type_omits_links(monkeypatch, provider):
    config = provider.validate_config({"base_url": BASE, "project": "tj"})
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 7})

    _install(monkeypatch, handler)

    provider.create_ticket(config, "tok", title="x", body_markdown="")

    assert "_links" not in captured["body"]


def test_create_work_package_surfaces_api_error(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(422, text="unprocessable"))

    with pytest.raises(ProviderRequestError):
        provider.create_ticket(config, "tok", title="x", body_markdown="")


def test_fetch_status_reads_embedded_name(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "_embedded": {"status": {"name": "Closed"}},
        "_links": {"self": {"href": "/api/v3/work_packages/9"}},
    }))

    ticket = provider.fetch_status(config, "tok", "9")

    assert ticket.status_raw == "Closed"
    assert ticket.status_normalized == "closed"


def test_fetch_status_falls_back_to_link_title(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "_links": {"status": {"title": "Resolved"}, "self": {"href": "/api/v3/work_packages/9"}},
    }))

    ticket = provider.fetch_status(config, "tok", "9")

    assert ticket.status_raw == "Resolved"
    assert ticket.status_normalized == "closed"


def test_fetch_status_unknown_when_404(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(404))

    ticket = provider.fetch_status(config, "tok", "999")

    assert ticket.status_normalized == "unknown"


def test_normalize_status_honors_custom_mapping(provider):
    assert provider.normalize_status("Triage", {"Triage": "open"}) == "open"
    assert provider.normalize_status("Rejected", {}) == "closed"
