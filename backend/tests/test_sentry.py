"""Sentry init + PII scrubbing in before_send."""
from unittest.mock import patch

import pytest

from testjam.core import sentry as sentry_module
from testjam.core.sentry import _before_send, configure_sentry


@pytest.fixture
def empty_environment(monkeypatch):
    for key in ("SENTRY_DSN", "SENTRY_ENVIRONMENT", "SENTRY_TRACES_SAMPLE_RATE"):
        monkeypatch.delenv(key, raising=False)


def test_init_is_skipped_when_dsn_is_unset(empty_environment):
    with patch.object(sentry_module, "sentry_sdk") as fake_sdk:
        configure_sentry()

    fake_sdk.init.assert_not_called()


def test_init_runs_when_dsn_provided(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/123")
    with patch.object(sentry_module, "sentry_sdk") as fake_sdk:
        configure_sentry()

    fake_sdk.init.assert_called_once()
    kwargs = fake_sdk.init.call_args.kwargs
    assert kwargs["dsn"] == "https://public@example.ingest.sentry.io/123"
    assert kwargs["send_default_pii"] is False
    assert kwargs["include_local_variables"] is False
    assert kwargs["max_request_body_size"] == "never"


def test_before_send_attaches_request_id_tag(monkeypatch):
    monkeypatch.setattr(sentry_module, "current_request_id", lambda: "abc-xyz")

    enriched = _before_send({}, {})

    assert enriched["tags"]["request_id"] == "abc-xyz"


def test_before_send_skips_tag_without_request_id(monkeypatch):
    monkeypatch.setattr(sentry_module, "current_request_id", lambda: None)

    enriched = _before_send({}, {})

    assert "tags" not in enriched


def test_before_send_scrubs_sensitive_headers():
    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer hunter2",
                "X-API-Key": "tj_secret",
                "Cookie": "session=...",
                "Content-Type": "application/json",
            },
        },
    }

    scrubbed = _before_send(event, {})

    assert scrubbed["request"]["headers"]["Authorization"] == "[scrubbed]"
    assert scrubbed["request"]["headers"]["X-API-Key"] == "[scrubbed]"
    assert scrubbed["request"]["headers"]["Cookie"] == "[scrubbed]"
    assert scrubbed["request"]["headers"]["Content-Type"] == "application/json"


def test_before_send_scrubs_password_fields_in_query_string():
    event = {
        "request": {
            "query_string": "username=alice&password=hunter2&keep=visible",
            "url": "https://api.example.com/login?password=hunter2&user=alice",
        },
    }

    scrubbed = _before_send(event, {})

    assert "password=%5Bscrubbed%5D" in scrubbed["request"]["query_string"]
    assert "keep=visible" in scrubbed["request"]["query_string"]
    assert "password=%5Bscrubbed%5D" in scrubbed["request"]["url"]
    assert scrubbed["request"]["url"].startswith("https://api.example.com/login?")


def test_before_send_scrubs_password_fields_in_body():
    event = {
        "request": {
            "data": {
                "username": "alice",
                "password": "hunter2",
                "new_password": "hunter3",
                "token": "reset-token-value",
            },
        },
    }

    scrubbed = _before_send(event, {})

    assert scrubbed["request"]["data"]["username"] == "alice"
    assert scrubbed["request"]["data"]["password"] == "[scrubbed]"
    assert scrubbed["request"]["data"]["new_password"] == "[scrubbed]"
    assert scrubbed["request"]["data"]["token"] == "[scrubbed]"
