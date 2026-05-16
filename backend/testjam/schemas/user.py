from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator


SUPPORTED_LOCALES = ("en", "es", "ca", "gl", "eu")


def _validate_iana_timezone(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {value!r}") from exc
    return value


def _validate_locale(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale: {value!r}")
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
    locale: str | None = None

    @field_validator("timezone")
    @classmethod
    def _timezone_must_be_iana(cls, value: str | None) -> str | None:
        return _validate_iana_timezone(value)

    @field_validator("locale")
    @classmethod
    def _locale_must_be_supported(cls, value: str | None) -> str | None:
        return _validate_locale(value)


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
    last_login_at: datetime | None = None
    timezone: str | None = None
    use_relative_dates: bool = True
    locale: str | None = None

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    timezone: str | None = None
    password: str | None = None
    clear_lockout: bool | None = None
    failed_login_count: int | None = None

    @field_validator("timezone")
    @classmethod
    def _timezone_must_be_iana(cls, value: str | None) -> str | None:
        return _validate_iana_timezone(value)


class ResetPasswordRequest(BaseModel):
    mode: Literal["email", "temporary_password"]


class ResetPasswordResponse(BaseModel):
    mode: Literal["email", "temporary_password"]
    temporary_password: str | None = None


class ActivityExecution(BaseModel):
    id: int
    project_id: int
    project_name: str
    title: str
    status: str
    created_at: datetime


class ActivityCase(BaseModel):
    id: int
    project_id: int
    project_name: str
    name: str
    created_at: datetime


class UserActivity(BaseModel):
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    recent_executions: list[ActivityExecution] = []
    recent_cases: list[ActivityCase] = []


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
