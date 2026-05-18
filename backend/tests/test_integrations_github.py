"""GitHubProvider adapter tests with an httpx MockTransport.

The transport is injected by monkeypatching httpx.Client inside the adapter
so we exercise the real adapter path (headers, URL shape, JSON handling)
without hitting api.github.com.
"""
import json

import httpx
import pytest

from testjam.services.integrations.base import (
    ProviderConfigError,
    ProviderRequestError,
)
from testjam.services.integrations.providers.github import GitHubProvider


GITHUB_BASE = "https://api.github.com"
REPO_PATH = "/repos/acme/awesome"


@pytest.fixture
def provider():
    return GitHubProvider()


@pytest.fixture
def config(provider):
    return provider.validate_config({"owner": "acme", "repo": "awesome"})


def _install(monkeypatch, handler):
    transport = httpx.MockTransport(handler)

    class StubClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(
        "testjam.services.integrations.providers.github.httpx.Client", StubClient,
    )


def test_validate_config_accepts_slash_form(provider):
    result = provider.validate_config({"repository": "acme/widgets"})

    assert result == {
        "owner": "acme", "repo": "widgets", "api_base": GITHUB_BASE,
    }


def test_validate_config_rejects_missing_owner(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({"repo": "widgets"})


def test_health_check_pings_repo(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"id": 1, "name": "awesome"})

    _install(monkeypatch, handler)

    provider.health_check(config, "tok_abc")

    assert captured["url"] == f"{GITHUB_BASE}{REPO_PATH}"
    assert captured["auth"] == "Bearer tok_abc"


def test_health_check_raises_on_404(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(404, json={"message": "Not Found"}))

    with pytest.raises(ProviderConfigError):
        provider.health_check(config, "tok")


def test_create_ticket_posts_issue(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={
            "number": 42, "html_url": "https://github.com/acme/awesome/issues/42",
            "state": "open",
        })

    _install(monkeypatch, handler)

    ticket = provider.create_ticket(
        config, "tok",
        title="Login broken", body_markdown="Steps…", labels=["bug", "p1"],
    )

    assert captured["method"] == "POST"
    assert captured["url"] == f"{GITHUB_BASE}{REPO_PATH}/issues"
    assert captured["body"]["title"] == "Login broken"
    assert captured["body"]["labels"] == ["bug", "p1"]
    assert ticket.external_id == "42"
    assert ticket.url == "https://github.com/acme/awesome/issues/42"
    assert ticket.status_normalized == "open"


def test_create_ticket_surfaces_api_error(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(422, text="validation failed"))

    with pytest.raises(ProviderRequestError):
        provider.create_ticket(config, "tok", title="x", body_markdown="")


def test_fetch_status_returns_closed_issue(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "state": "closed", "html_url": "https://github.com/acme/awesome/issues/7",
    }))

    ticket = provider.fetch_status(config, "tok", "7")

    assert ticket.status_raw == "closed"
    assert ticket.status_normalized == "closed"


def test_fetch_status_unknown_when_404(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(404))

    ticket = provider.fetch_status(config, "tok", "999")

    assert ticket.status_normalized == "unknown"


def test_fetch_status_network_error_raises(monkeypatch, provider, config):
    def handler(request):
        raise httpx.ConnectError("network down")

    _install(monkeypatch, handler)

    with pytest.raises(ProviderRequestError):
        provider.fetch_status(config, "tok", "5")
