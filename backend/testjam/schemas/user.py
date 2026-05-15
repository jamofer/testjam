from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator


def _validate_iana_timezone(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {value!r}") from exc
    return value


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    password: str | None = None
    failed_login_count: int | None = None
    clear_lockout: bool | None = None
    timezone: str | None = None
    use_relative_dates: bool | None = None

    @field_validator("timezone")
    @classmethod
    def _timezone_must_be_iana(cls, value: str | None) -> str | None:
        return _validate_iana_timezone(value)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class OwnedProjectAction(BaseModel):
    project_id: int
    action: Literal["reassign", "archive"]
    new_owner_id: int | None = None


class UserDeleteRequest(BaseModel):
    owned_projects: list[OwnedProjectAction] = Field(default_factory=list)


class UnresolvedOwnedProject(BaseModel):
    project_id: int
    project_name: str
    candidate_member_ids: list[int]


class UserOut(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    deleted_at: datetime | None = None
    timezone: str | None = None
    use_relative_dates: bool = True

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GroupMemberOut(BaseModel):
    user_id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


class GroupMemberUpdate(BaseModel):
    role: str


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class GroupOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    members: list[GroupMemberOut] = []

    model_config = {"from_attributes": True}
