"""Shapes of the main API responses, for type checkers and editor completion.

Responses are still plain ``dict`` objects at runtime; these ``TypedDict``
classes only describe the keys. Timestamps arrive as ISO 8601 strings. Keys
are optional (``total=False``) so newer servers can add fields freely.
"""
from __future__ import annotations

from typing import Any, TypedDict

from testjam_client.statuses import ExecutionStatus, ResultStatus


class Project(TypedDict, total=False):
    id: int
    name: str
    description: str | None
    created_at: str
    updated_at: str
    archived_at: str | None
    suite_count: int
    case_count: int
    execution_count: int
    last_execution_at: str | None
    recent_executions: list[dict[str, Any]]


class User(TypedDict, total=False):
    id: int
    username: str
    email: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    created_at: str
    last_login_at: str | None
    timezone: str | None
    locale: str | None


class Suite(TypedDict, total=False):
    id: int
    project_id: int
    name: str
    description: str | None
    tags: list[str]
    parent_suite_id: int | None
    child_suite_ids: list[int]
    test_case_ids: list[int]
    steps: list[dict[str, Any]]
    created_at: str
    updated_at: str


class TestCase(TypedDict, total=False):
    id: int
    suite_id: int
    name: str
    description: str | None
    tags: list[str]
    preconditions: str | None
    external_id: str | None
    steps: list[dict[str, Any]]
    attachments: list[Attachment]
    custom_fields: dict[str, Any]
    archived_at: str | None
    created_at: str
    updated_at: str


class Attachment(TypedDict, total=False):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    url: str
    created_at: str


class ExecutionSummary(TypedDict, total=False):
    total: int
    passed: int
    failed: int
    blocked: int
    not_run: int


class Execution(TypedDict, total=False):
    id: int
    project_id: int
    title: str
    description: str | None
    type: str
    status: ExecutionStatus
    version_id: int | None
    version_name: str | None
    environment: str | None
    triggered_by: str | None
    started_at: str | None
    finished_at: str | None
    created_at: str
    summary: ExecutionSummary
    attachments: list[Attachment]
    custom_fields: dict[str, Any]


class StepResult(TypedDict, total=False):
    id: int
    test_result_id: int
    step_id: int | None
    step_action: str | None
    step_expected_result: str | None
    status: ResultStatus
    comment: str | None
    duration_ms: int | None
    started_at: str | None
    log_output: str | None


class Result(TypedDict, total=False):
    id: int
    execution_id: int
    test_case_id: int | None
    test_case_title: str | None
    status: ResultStatus
    comment: str | None
    executed_by: str | None
    executed_at: str | None
    duration_ms: int | None
    assigned_to_id: int | None
    step_results: list[StepResult]
    attachments: list[Attachment]


class BulkResultResponse(TypedDict):
    created: int
    updated: int
    errors: list[dict[str, Any]]


class CaseImportError(TypedDict):
    row: int
    name: str
    error: str


class CaseImportReport(TypedDict):
    created: int
    suites_created: int
    errors: list[CaseImportError]
