from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _validate_slug(value: str) -> str:
    if not SLUG_PATTERN.match(value):
        raise ValueError(
            "slug must be lowercase alphanumeric with hyphens (1-64 chars, no leading/trailing hyphen)"
        )
    return value


def _validate_color(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if not HEX_COLOR_PATTERN.match(value):
        raise ValueError("color must be a hex value like #10b981 or #abc")
    return value


class EnvironmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)
    description: str | None = None
    host: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=16)
    is_default: bool = False

    _slug = field_validator("slug")(lambda cls, v: _validate_slug(v))
    _color = field_validator("color")(lambda cls, v: _validate_color(v))


class EnvironmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    slug: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None
    host: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=16)
    is_default: bool | None = None

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_slug(value)

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        return _validate_color(value)


class EnvironmentOut(BaseModel):
    id: int
    project_id: int
    name: str
    slug: str
    description: str | None
    host: str | None
    color: str | None
    order: int
    is_default: bool
    archived_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EnvironmentReorder(BaseModel):
    ids: list[int]
