"""JSON formatter + request_id middleware."""
import json
import logging
import uuid

import pytest

from testjam.core.logging import (
    REQUEST_ID_HEADER,
    JsonFormatter,
    current_request_id,
    set_current_user_id,
    _request_id,
    _user_id,
)


@pytest.fixture
def reset_context():
    request_token = _request_id.set(None)
    user_token = _user_id.set(None)
    yield
    _request_id.reset(request_token)
    _user_id.reset(user_token)


def _format(record: logging.LogRecord) -> dict:
    return json.loads(JsonFormatter().format(record))


def _make_record(message: str = "hello", **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="testjam.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formatter_emits_iso_timestamp_level_logger_msg():
    record = _make_record("hello world")

    payload = _format(record)

    assert payload["msg"] == "hello world"
    assert payload["level"] == "info"
    assert payload["logger"] == "testjam.test"
    assert payload["ts"].endswith("Z")


def test_formatter_includes_request_id_when_set(reset_context):
    _request_id.set("abc-123")
    record = _make_record()

    payload = _format(record)

    assert payload["request_id"] == "abc-123"


def test_formatter_omits_request_id_when_unset(reset_context):
    record = _make_record()

    payload = _format(record)

    assert "request_id" not in payload


def test_formatter_includes_user_id_only_when_set(reset_context):
    _user_id.set(42)
    record = _make_record()

    payload = _format(record)

    assert payload["user_id"] == 42


def test_formatter_passes_through_extra_fields():
    record = _make_record("done", path="/api/v1/projects", status=200, latency_ms=12)

    payload = _format(record)

    assert payload["path"] == "/api/v1/projects"
    assert payload["status"] == 200
    assert payload["latency_ms"] == 12


def test_response_includes_request_id_header(client):
    response = client.get("/health")

    request_id = response.headers.get(REQUEST_ID_HEADER)
    assert request_id
    assert len(request_id) == 32
    uuid.UUID(hex=request_id)


def test_inbound_request_id_header_is_propagated_back(client):
    incoming = "client-supplied-correlation-id"

    response = client.get("/health", headers={REQUEST_ID_HEADER: incoming})

    assert response.headers[REQUEST_ID_HEADER] == incoming


def test_authenticated_request_records_user_id_in_context(auth_client):
    auth_client.get("/api/v1/users/me")

    assert isinstance(current_request_id(), (str, type(None)))
