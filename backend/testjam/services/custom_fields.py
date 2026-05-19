from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from testjam.models.custom_field import CustomFieldDefinition
from testjam.schemas.custom_field import _validate_value_against_type


def validate_payload(
    db: Session,
    project_id: int,
    entity_type: str,
    payload: dict[str, Any] | None,
    *,
    is_create: bool,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    definitions = _active_definitions(db, project_id, entity_type)
    result: dict[str, Any] = dict(existing or {})
    incoming = dict(payload or {})

    for definition in definitions:
        if definition.key in incoming:
            value = incoming[definition.key]
            if value is None:
                result.pop(definition.key, None)
                continue
            _validate_value(definition, value)
            result[definition.key] = value
        elif is_create:
            _apply_default_or_require(definition, result)

    return result


def next_position(db: Session, project_id: int, entity_type: str) -> int:
    last = (
        db.query(CustomFieldDefinition.position)
        .filter(
            CustomFieldDefinition.project_id == project_id,
            CustomFieldDefinition.entity_type == entity_type,
        )
        .order_by(CustomFieldDefinition.position.desc())
        .first()
    )
    return (last[0] + 1) if last else 0


def _active_definitions(
    db: Session, project_id: int, entity_type: str
) -> list[CustomFieldDefinition]:
    return (
        db.query(CustomFieldDefinition)
        .filter(
            CustomFieldDefinition.project_id == project_id,
            CustomFieldDefinition.entity_type == entity_type,
            CustomFieldDefinition.archived_at.is_(None),
        )
        .order_by(CustomFieldDefinition.position.asc(), CustomFieldDefinition.id.asc())
        .all()
    )


def _validate_value(definition: CustomFieldDefinition, value: Any) -> None:
    allowed_option_values = _option_values(definition)
    try:
        _validate_value_against_type(
            definition.type, value, allowed_option_values, label=definition.key
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["custom_fields", definition.key],
                    "msg": str(exc),
                    "type": "value_error",
                }
            ],
        ) from exc


def _apply_default_or_require(
    definition: CustomFieldDefinition, result: dict[str, Any]
) -> None:
    if definition.key in result:
        return
    if definition.default_value is not None:
        result[definition.key] = definition.default_value
        return
    if definition.required:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["custom_fields", definition.key],
                    "msg": "field is required",
                    "type": "value_error.missing",
                }
            ],
        )


def _option_values(definition: CustomFieldDefinition) -> set[str]:
    options = definition.options or []
    return {option["value"] for option in options if "value" in option}
