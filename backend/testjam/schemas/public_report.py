from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


PublicReportKind = Literal["bug_report", "execution"]


class PublicReportCreate(BaseModel):
    kind: PublicReportKind
    label: str | None = Field(default=None, max_length=128)
    execution_id: int | None = None
    version_id: int | None = None
    environment: str | None = Field(default=None, max_length=64)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def _check_kind_requirements(self) -> "PublicReportCreate":
        if self.kind == "execution" and self.execution_id is None:
            raise ValueError("execution_id is required when kind='execution'")
        if self.kind == "bug_report" and self.execution_id is not None:
            raise ValueError("execution_id is only valid when kind='execution'")
        return self


class PublicReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    kind: PublicReportKind
    label: str | None
    execution_id: int | None
    version_id: int | None
    environment: str | None
    created_by_id: int | None
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    last_viewed_at: datetime | None
    view_count: int


class PublicReportCreated(PublicReportOut):
    token: str
    url_path: str
