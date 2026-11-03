"""Login endpoint rejects after exceeding the per-IP rate limit."""
import pytest
from starlette.requests import Request

from testjam.core import rate_limit
from testjam.core.config import settings
from testjam.core.rate_limit import LOGIN_RATE_LIMIT, limiter
from testjam.models.settings import AppSettings
from tests.conftest import TestingSession

LIMIT_PER_WINDOW = int(LOGIN_RATE_LIMIT.split("/")[0])
PROXIED_CLIENT = "203.0.113.10"
OTHER_PROXIED_CLIENT = "203.0.113.20"
PEER_ADDRESS = "172.18.0.5"


@pytest.fixture
def rate_limited_client(client):
    limiter.reset()
    limiter.enabled = True
    yield client
    limiter.enabled = False
    limiter.reset()


@pytest.fixture
def ip_throttle_enabled():
    with TestingSession() as db:
        row = db.get(AppSettings, 1)
        row.ip_throttle_enabled = True
        db.commit()


def _attempt_login(client):
    return client.post(
        "/api/v1/auth/login",
        data={"username": "nobody", "password": "wrong"},
    )


def test_login_allows_up_to_limit_then_returns_429(rate_limited_client):
    for _ in range(LIMIT_PER_WINDOW):
        response = _attempt_login(rate_limited_client)
        assert response.status_code == 401

    blocked = _attempt_login(rate_limited_client)

    assert blocked.status_code == 429


def test_login_returns_423_when_ip_throttle_enabled(client, ip_throttle_enabled):
    statuses = [_attempt_login(client).status_code for _ in range(LIMIT_PER_WINDOW + 3)]

    assert statuses[:LIMIT_PER_WINDOW] == [401] * LIMIT_PER_WINDOW
    assert all(code == 423 for code in statuses[LIMIT_PER_WINDOW:])


def test_login_skips_ip_throttle_when_disabled(client):
    statuses = [_attempt_login(client).status_code for _ in range(LIMIT_PER_WINDOW + 3)]

    assert all(code == 401 for code in statuses)


def test_spoofed_forwarded_for_does_not_evade_login_limit(rate_limited_client):
    responses = [
        _attempt_login_from(rate_limited_client, f"10.0.0.{attempt}, {PROXIED_CLIENT}")
        for attempt in range(LIMIT_PER_WINDOW + 1)
    ]

    assert responses[-1].status_code == 429


def test_clients_behind_the_proxy_are_limited_separately(rate_limited_client):
    for _ in range(LIMIT_PER_WINDOW + 1):
        _attempt_login_from(rate_limited_client, PROXIED_CLIENT)

    response = _attempt_login_from(rate_limited_client, OTHER_PROXIED_CLIENT)

    assert response.status_code != 429


def test_client_ip_uses_last_entry_appended_by_the_proxy():
    assert rate_limit.client_ip(_request(f"1.1.1.1, {PROXIED_CLIENT}")) == PROXIED_CLIENT


def test_client_ip_honours_additional_trusted_proxies(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 2)

    client = rate_limit.client_ip(_request(f"1.1.1.1, {PROXIED_CLIENT}, {OTHER_PROXIED_CLIENT}"))

    assert client == PROXIED_CLIENT


def test_client_ip_ignores_header_without_trusted_proxies(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 0)

    assert rate_limit.client_ip(_request("1.1.1.1")) == PEER_ADDRESS


def test_client_ip_uses_peer_when_header_is_absent():
    assert rate_limit.client_ip(_request(None)) == PEER_ADDRESS


def _attempt_login_from(client, forwarded_for: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": "ghost", "password": "wrong"},
        headers={"X-Forwarded-For": forwarded_for},
    )


def _request(forwarded_for: str | None) -> Request:
    headers = [(b"x-forwarded-for", forwarded_for.encode())] if forwarded_for else []
    return Request({"type": "http", "headers": headers, "client": (PEER_ADDRESS, 1234)})
