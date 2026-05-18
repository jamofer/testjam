from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectIntegrationCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    config: dict[str, Any] = Field(default_factory=dict)
    status_mapping: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    secret: str = Field(min_length=1)


class ProjectIntegrationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    config: dict[str, Any] | None = None
    status_mapping: dict[str, str] | None = None
    is_active: bool | None = None


class IntegrationCredentialRotate(BaseModel):
    secret: str = Field(min_length=1)


class ProjectIntegrationOut(BaseModel):
    id: int
    project_id: int
    provider: str
    name: str
    config: dict[str, Any]
    status_mapping: dict[str, str]
    is_active: bool
    has_credential: bool
    credential_expires_at: datetime | None = None
    credential_last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntegrationProviderDescriptor(BaseModel):
    key: str
    label: str


class BugExternalLinkCreate(BaseModel):
    integration_id: int
    labels: list[str] = Field(default_factory=list)


class BugExternalLinkOut(BaseModel):
    id: int
    bug_id: int
    integration_id: int | None
    provider: str | None
    external_id: str
    url: str
    status_raw: str | None
    status_normalized: str
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResultReportRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: str = "medium"
    tags: list[str] | None = None
    integration_id: int | None = None
    labels: list[str] = Field(default_factory=list)


class ResultReportResponse(BaseModel):
    bug_id: int
    bug_number: int
    external_link: BugExternalLinkOut | None = None
