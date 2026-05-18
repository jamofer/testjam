"""GitLabProvider tests with httpx MockTransport."""
import json

import httpx
import pytest

from testjam.services.integrations.base import (
    ProviderConfigError,
    ProviderRequestError,
)
from testjam.services.integrations.providers.gitlab import GitLabProvider


GITLAB = "https://gitlab.com"
PROJECT_PATH = quote_path = "acme%2Fawesome"


@pytest.fixture
def provider():
    return GitLabProvider()


@pytest.fixture
def config(provider):
    return provider.validate_config({"project": "acme/awesome"})


def _install(monkeypatch, handler):
    transport = httpx.MockTransport(handler)

    class StubClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(
        "testjam.services.integrations.providers.gitlab.httpx.Client", StubClient,
    )


def test_validate_config_requires_project(provider):
    with pytest.raises(ProviderConfigError):
        provider.validate_config({})


def test_validate_config_accepts_numeric_id(provider):
    result = provider.validate_config({"project": "42"})

    assert result == {"project": "42", "base_url": GITLAB}


def test_validate_config_strips_trailing_slash_in_base(provider):
    result = provider.validate_config({
        "project": "acme/x", "base_url": "https://git.acme.io/",
    })

    assert result["base_url"] == "https://git.acme.io"


def test_health_check_sends_private_token(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["token"] = request.headers.get("private-token")
        return httpx.Response(200, json={"id": 1})

    _install(monkeypatch, handler)

    provider.health_check(config, "glpat_abc")

    assert captured["url"] == f"{GITLAB}/api/v4/projects/{PROJECT_PATH}"
    assert captured["token"] == "glpat_abc"


def test_health_check_raises_on_404(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(404))

    with pytest.raises(ProviderConfigError):
        provider.health_check(config, "tok")


def test_create_ticket_posts_to_issues_endpoint(monkeypatch, provider, config):
    captured = {}

    def handler(request):
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={
            "iid": 7,
            "web_url": "https://gitlab.com/acme/awesome/-/issues/7",
            "state": "opened",
        })

    _install(monkeypatch, handler)

    ticket = provider.create_ticket(
        config, "tok",
        title="Login broken", body_markdown="Steps…", labels=["bug", "p1"],
    )

    assert captured["method"] == "POST"
    assert captured["url"] == f"{GITLAB}/api/v4/projects/{PROJECT_PATH}/issues"
    assert captured["body"]["title"] == "Login broken"
    assert captured["body"]["labels"] == "bug,p1"
    assert ticket.external_id == "7"
    assert ticket.url == "https://gitlab.com/acme/awesome/-/issues/7"
    assert ticket.status_normalized == "open"


def test_create_ticket_surfaces_api_error(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(400, text="missing scope"))

    with pytest.raises(ProviderRequestError):
        provider.create_ticket(config, "tok", title="x", body_markdown="")


def test_fetch_status_closed(monkeypatch, provider, config):
    _install(monkeypatch, lambda request: httpx.Response(200, json={
        "state": "closed",
        "web_url": "https://gitlab.com/acme/awesome/-/issues/9",
    }))

    ticket = provider.fetch_status(config, "tok", "9")

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
