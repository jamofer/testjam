from datetime import datetime
from pydantic import BaseModel

VALID_ROLES = {"owner", "tester", "viewer"}


class ProjectMemberAdd(BaseModel):
    user_id: int
    role: str


class ProjectMemberUpdate(BaseModel):
    role: str


class ProjectMemberOut(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: str | None
    role: str
    added_at: datetime
