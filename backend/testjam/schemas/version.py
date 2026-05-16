from datetime import date, datetime
from pydantic import BaseModel


class ProjectVersionCreate(BaseModel):
    name: str
    description: str | None = None
    status: str = "active"
    vcs_tag: str | None = None
    release_date: date | None = None


class ProjectVersionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    vcs_tag: str | None = None
    release_date: date | None = None


class ProjectVersionOut(BaseModel):
    id: int
    project_id: int
    name: str
    description: str | None
    status: str
    vcs_tag: str | None
    release_date: date | None
    released_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
