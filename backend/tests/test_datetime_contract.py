"""ISO 8601 contract: every datetime in API payloads carries an offset.

Walks JSON payloads from representative endpoints and asserts that any string
that looks like a datetime ends in ``Z`` or ``+HH:MM`` / ``-HH:MM``.
"""
from __future__ import annotations

import re

DATETIME_LIKE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
OFFSET_SUFFIX = re.compile(r"(Z|[+\-]\d{2}:\d{2})$")


def test_user_me_datetimes_have_offset(auth_client):
    payload = auth_client.get("/api/v1/users/me").json()
    _assert_offsets(payload)


def test_project_datetimes_have_offset(auth_client, project_id):
    payload = auth_client.get(f"/api/v1/projects/{project_id}").json()
    _assert_offsets(payload)


def test_case_datetimes_have_offset(auth_client, case_ids):
    payload = auth_client.get(f"/api/v1/cases/{case_ids[0]}").json()
    _assert_offsets(payload)


def test_execution_datetimes_have_offset(auth_client, execution_with_step):
    execution_id, _, _ = execution_with_step

    payload = auth_client.get(f"/api/v1/executions/{execution_id}").json()

    _assert_offsets(payload)


def test_token_datetimes_have_offset(auth_client):
    created = auth_client.post("/api/v1/users/me/tokens", json={"name": "tok"}).json()

    payload = auth_client.get("/api/v1/users/me/tokens").json()

    _assert_offsets(payload)
    assert created["prefix"]


def _assert_offsets(node):
    if isinstance(node, dict):
        for key, value in node.items():
            _assert_offsets(value)
    elif isinstance(node, list):
        for item in node:
            _assert_offsets(item)
    elif isinstance(node, str) and DATETIME_LIKE.match(node):
        assert OFFSET_SUFFIX.search(node), f"datetime without offset: {node!r}"
