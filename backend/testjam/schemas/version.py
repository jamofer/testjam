from datetime import date, datetime
from pydantic import BaseModel, Field, computed_field

from testjam.core.config import settings
from testjam.schemas.user import UserOut


class VersionAttachmentOut(BaseModel):
    id: int
    filename: str
    content_type: str | None
    size_bytes: int | None
    uploaded_at: datetime
    uploaded_by: UserOut | None = None
    version_id: int | None = Field(default=None, exclude=True)
    file_path: str | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def url(self) -> str:
        if self.version_id is None:
            return ""
        return f"{settings.API_V1_PREFIX}/versions/{self.version_id}/attachments/{self.id}/download"

    model_config = {"from_attributes": True}


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
