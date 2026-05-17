from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from testjam.schemas.user import UserOut


BugSeverity = Literal["critical", "high", "medium", "low"]
BugStatus = Literal[
    "open",
    "in_progress",
    "resolved",
    "closed",
    "wont_fix",
    "not_a_bug",
]
TERMINAL_BUG_STATUSES = {"resolved", "closed", "wont_fix", "not_a_bug"}

BugLinkKind = Literal["relates_to", "blocks", "blocked_by", "duplicate_of"]

RECIPROCAL_LINK_KIND: dict[str, str] = {
    "relates_to": "relates_to",
    "blocks": "blocked_by",
    "blocked_by": "blocks",
    "duplicate_of": "duplicate_of",
}


class BugCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: BugSeverity = "medium"
    tags: list[str] | None = None
    result_id: int | None = None
    execution_id: int | None = None
    version_id: int | None = None
    fixed_in_version_id: int | None = None
    environment: str | None = None
    assigned_to_id: int | None = None


class BugUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    severity: BugSeverity | None = None
    tags: list[str] | None = None
    version_id: int | None = None
    fixed_in_version_id: int | None = None
    environment: str | None = None
    assigned_to_id: int | None = None
    external_ticket_url: str | None = None


class BugStatusChange(BaseModel):
    status: BugStatus
    note: str | None = None


class BugOut(BaseModel):
    id: int
    project_id: int
    number: int
    title: str
    description: str | None
    severity: BugSeverity
    status: BugStatus
    tags: list[str] | None = None
    result_id: int | None
    execution_id: int | None
    version_id: int | None
    version_name: str | None = None
    fixed_in_version_id: int | None = None
    fixed_in_version_name: str | None = None
    environment: str | None
    external_ticket_url: str | None
    assigned_to: UserOut | None = None
    created_by: UserOut | None = None
    updated_by: UserOut | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class BugCommentCreate(BaseModel):
    body: str = Field(min_length=1)


class BugCommentUpdate(BaseModel):
    body: str = Field(min_length=1)


class BugCommentOut(BaseModel):
    id: int
    bug_id: int
    body: str
    created_by: UserOut | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BugAttachmentOut(BaseModel):
    id: int
    bug_id: int
    filename: str
    content_type: str | None
    size_bytes: int | None
    uploaded_by: UserOut | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class BugStatusHistoryOut(BaseModel):
    id: int
    bug_id: int
    from_status: BugStatus | None
    to_status: BugStatus
    note: str | None
    changed_by: UserOut | None = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class BugLinkCreate(BaseModel):
    kind: BugLinkKind | None = None
    label: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=1024)
    execution_id: int | None = None
    test_case_id: int | None = None
    test_step_id: int | None = None
    target_bug_id: int | None = None

    @model_validator(mode="after")
    def _at_least_one_target(self):
        if not (self.url or self.execution_id or self.test_case_id or self.target_bug_id):
            raise ValueError(
                "Provide url, execution_id, test_case_id or target_bug_id",
            )
        if self.kind is not None and self.target_bug_id is None:
            raise ValueError("kind requires target_bug_id")
        return self


class BugContextNode(BaseModel):
    id: int
    name: str


class BugContextExecution(BaseModel):
    id: int
    title: str


class BugContextStep(BaseModel):
    id: int
    action: str


class BugLinkOut(BaseModel):
    id: int
    bug_id: int
    kind: BugLinkKind | None = None
    label: str | None
    url: str | None
    execution_id: int | None
    test_case_id: int | None
    test_step_id: int | None
    target_bug_id: int | None
    execution_title: str | None = None
    execution_environment: str | None = None
    execution_version_id: int | None = None
    execution_version_name: str | None = None
    suite_path: list[BugContextNode] = []
    test_case_name: str | None = None
    test_step_action: str | None = None
    target_bug_number: int | None = None
    target_bug_title: str | None = None
    created_by: UserOut | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BugContextOut(BaseModel):
    execution: BugContextExecution | None = None
    suite_path: list[BugContextNode] = []
    case: BugContextNode | None = None
    step: BugContextStep | None = None
    version_id: int | None = None
    version_name: str | None = None
    environment: str | None = None
