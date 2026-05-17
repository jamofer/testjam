from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

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


class BugCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: BugSeverity = "medium"
    tags: list[str] | None = None
    result_id: int | None = None
    execution_id: int | None = None
    version_id: int | None = None
    environment: str | None = None
    assigned_to_id: int | None = None


class BugUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    severity: BugSeverity | None = None
    tags: list[str] | None = None
    version_id: int | None = None
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
    environment: str | None
    external_ticket_url: str | None
    assigned_to: UserOut | None = None
    created_by: UserOut | None = None
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
