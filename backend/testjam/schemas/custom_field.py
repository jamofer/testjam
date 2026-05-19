from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


CustomFieldEntityType = Literal["bug", "test_case", "execution"]
CustomFieldType = Literal[
    "text", "number", "bool", "single_select", "multi_select", "date"
]
SELECT_TYPES: set[str] = {"single_select", "multi_select"}

KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,62}[a-z0-9]$|^[a-z]$")
HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


class CustomFieldOption(BaseModel):
    value: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=128)
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not HEX_COLOR_PATTERN.match(value):
            raise ValueError("color must be a hex value like #10b981 or #abc")
        return value


def _validate_options(value: list[CustomFieldOption] | None) -> list[CustomFieldOption] | None:
    if value is None:
        return None
    values = [option.value for option in value]
    if len(values) != len(set(values)):
        raise ValueError("option values must be unique")
    return value


def _validate_key(value: str) -> str:
    if not KEY_PATTERN.match(value):
        raise ValueError(
            "key must be lowercase alphanumeric with underscores (start with a letter)"
        )
    return value


class CustomFieldDefinitionCreate(BaseModel):
    entity_type: CustomFieldEntityType
    key: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=128)
    type: CustomFieldType
    options: list[CustomFieldOption] | None = None
    required: bool = False
    default_value: Any | None = None

    _key = field_validator("key")(lambda cls, v: _validate_key(v))
    _options = field_validator("options")(lambda cls, v: _validate_options(v))

    @model_validator(mode="after")
    def _check_consistency(self):
        _enforce_options_rule(self.type, self.options)
        _enforce_default_value(self.type, self.options, self.default_value)
        _enforce_execution_required(self.entity_type, self.required, self.default_value)
        return self


class CustomFieldDefinitionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=128)
    options: list[CustomFieldOption] | None = None
    required: bool | None = None
    default_value: Any | None = None

    _options = field_validator("options")(lambda cls, v: _validate_options(v))


class CustomFieldDefinitionOut(BaseModel):
    id: int
    project_id: int
    entity_type: CustomFieldEntityType
    key: str
    label: str
    type: CustomFieldType
    options: list[CustomFieldOption] | None = None
    required: bool
    default_value: Any | None = None
    position: int
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomFieldReorder(BaseModel):
    ids: list[int]


def _enforce_options_rule(
    field_type: str, options: list[CustomFieldOption] | None
) -> None:
    if field_type in SELECT_TYPES:
        if not options:
            raise ValueError(f"options required for type '{field_type}'")
    elif options:
        raise ValueError(f"options not allowed for type '{field_type}'")


def _enforce_default_value(
    field_type: str,
    options: list[CustomFieldOption] | None,
    default_value: Any | None,
) -> None:
    if default_value is None:
        return
    allowed_option_values = (
        {option.value for option in options} if options else set()
    )
    _validate_value_against_type(
        field_type, default_value, allowed_option_values, label="default_value"
    )


def _enforce_execution_required(
    entity_type: str, required: bool, default_value: Any | None
) -> None:
    if entity_type == "execution" and required and default_value is None:
        raise ValueError(
            "required custom fields on executions must have a default_value"
        )


def _validate_value_against_type(
    field_type: str,
    value: Any,
    allowed_option_values: set[str],
    label: str = "value",
) -> None:
    if field_type == "text":
        if not isinstance(value, str):
            raise ValueError(f"{label} must be a string")
    elif field_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} must be a number")
    elif field_type == "bool":
        if not isinstance(value, bool):
            raise ValueError(f"{label} must be a boolean")
    elif field_type == "single_select":
        if not isinstance(value, str) or value not in allowed_option_values:
            raise ValueError(f"{label} must be one of the configured options")
    elif field_type == "multi_select":
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item in allowed_option_values for item in value
        ):
            raise ValueError(
                f"{label} must be a list of configured option values"
            )
    elif field_type == "date":
        if not isinstance(value, str):
            raise ValueError(f"{label} must be an ISO date string (YYYY-MM-DD)")
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(
                f"{label} must be an ISO date string (YYYY-MM-DD)"
            ) from exc
