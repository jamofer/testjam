"""SDK AboutResource — maps `/about` JSON onto the ServerAbout dataclass.

Uses a tiny `httpx.MockTransport` so the test stays decoupled from the
backend in-process app — `/about` is public, so there is nothing to
exercise on the server side beyond the JSON shape.
"""
from __future__ import annotations

import httpx

from testjam_client import TestjamClient
from testjam_client.resources.about import ServerAbout


SAMPLE = {
    "version": "1.0.0",
    "ref": "v1.0.0",
    "commit": "abc1234",
    "built_at": "2026-05-25T12:00:00Z",
}


def test_get_returns_serveraobout_dataclass():
    sdk = _client_with_about(SAMPLE)

    result = sdk.about.get()

    assert isinstance(result, ServerAbout)
    assert result == ServerAbout(**SAMPLE)


def test_get_does_not_require_authentication():
    sdk = _client_with_about(SAMPLE)
    assert "Authorization" not in sdk._http.headers
    assert "X-API-Key" not in sdk._http.headers

    sdk.about.get()


def test_dataclass_is_immutable():
    payload = ServerAbout(**SAMPLE)
    try:
        payload.version = "2.0.0"
    except Exception:
        return
    raise AssertionError("ServerAbout should be frozen")


def _client_with_about(payload):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/about")
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url="http://testserver/api/v1", transport=transport)
    return TestjamClient(http=http)
