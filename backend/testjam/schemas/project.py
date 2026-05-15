from datetime import datetime
from pydantic import BaseModel
from testjam.schemas.user import UserOut


class ProjectBase(BaseModel):
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RecentExecutionSummary(BaseModel):
    id: int
    title: str
    status: str
    started_at: datetime | None = None
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    not_run: int = 0


class ProjectOut(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    suite_count: int = 0
    case_count: int = 0
    execution_count: int = 0
    last_execution_at: datetime | None = None
    recent_executions: list[RecentExecutionSummary] = []

    model_config = {"from_attributes": True}


class ProjectMemberOut(BaseModel):
    user_id: int
    username: str
    role: str
    added_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberUpdate(BaseModel):
    role: str


class AdminProjectRow(BaseModel):
    id: int
    name: str
    description: str | None = None
    archived_at: datetime | None = None
    owner_id: int | None = None
    owner_username: str | None = None
    member_count: int = 0
    case_count: int = 0
    last_execution_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransferOwnershipRequest(BaseModel):
    new_owner_id: int
