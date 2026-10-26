from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    AuthContext,
    authorize_project,
    get_auth_context,
    require_project_access,
    require_project_writer,
    require_writable_project_access,
)
from testjam.database import get_db
from testjam.models.custom_field import CustomFieldDefinition
from testjam.models.project import Project
from testjam.models.user import User
from testjam.schemas.custom_field import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionOut,
    CustomFieldDefinitionUpdate,
    CustomFieldReorder,
    REQUIRES_DEFAULT_ENTITY_TYPES,
    SELECT_TYPES,
)
from testjam.services import custom_fields as custom_field_service


projects_router = APIRouter(prefix="/projects", tags=["Custom Fields"])
custom_fields_router = APIRouter(prefix="/custom-fields", tags=["Custom Fields"])


@projects_router.get(
    "/{id}/custom-fields", response_model=list[CustomFieldDefinitionOut]
)
def list_custom_fields(
    id: int,
    entity_type: str,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    query = db.query(CustomFieldDefinition).filter(
        CustomFieldDefinition.project_id == id,
        CustomFieldDefinition.entity_type == entity_type,
    )
    if not include_archived:
        query = query.filter(CustomFieldDefinition.archived_at.is_(None))
    return (
        query.order_by(
            CustomFieldDefinition.position.asc(), CustomFieldDefinition.id.asc()
        )
        .all()
    )


@projects_router.post(
    "/{id}/custom-fields",
    response_model=CustomFieldDefinitionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_custom_field(
    id: int,
    body: CustomFieldDefinitionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_writable_project_access),
):
    definition = CustomFieldDefinition(
        project_id=id,
        entity_type=body.entity_type,
        key=body.key,
        label=body.label,
        type=body.type,
        options=[option.model_dump() for option in body.options] if body.options else None,
        required=body.required,
        default_value=body.default_value,
        position=custom_field_service.next_position(db, id, body.entity_type),
    )
    db.add(definition)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Custom field key already exists"
        )
    db.commit()
    db.refresh(definition)
    return definition


@projects_router.post(
    "/{id}/custom-fields/reorder",
    response_model=list[CustomFieldDefinitionOut],
)
def reorder_custom_fields(
    id: int,
    body: CustomFieldReorder,
    db: Session = Depends(get_db),
    _: User = Depends(require_writable_project_access),
):
    rows = (
        db.query(CustomFieldDefinition)
        .filter(
            CustomFieldDefinition.project_id == id,
            CustomFieldDefinition.id.in_(body.ids),
        )
        .all()
    )
    if len(rows) != len(body.ids):
        raise HTTPException(
            status_code=400,
            detail="ids must reference custom fields of this project",
        )
    entity_types = {row.entity_type for row in rows}
    if len(entity_types) != 1:
        raise HTTPException(
            status_code=400,
            detail="reorder requires custom fields of the same entity_type",
        )
    order_map = {field_id: index for index, field_id in enumerate(body.ids)}
    for row in rows:
        row.position = order_map[row.id]
    db.commit()
    return (
        db.query(CustomFieldDefinition)
        .filter(
            CustomFieldDefinition.project_id == id,
            CustomFieldDefinition.entity_type == entity_types.pop(),
        )
        .order_by(
            CustomFieldDefinition.position.asc(), CustomFieldDefinition.id.asc()
        )
        .all()
    )


@custom_fields_router.get(
    "/{id}", response_model=CustomFieldDefinitionOut
)
def get_custom_field(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    definition = _get_definition(db, id)
    authorize_project(db, ctx, definition.project_id)
    return definition


@custom_fields_router.put(
    "/{id}", response_model=CustomFieldDefinitionOut
)
def update_custom_field(
    id: int,
    body: CustomFieldDefinitionUpdate,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    definition = _get_definition(db, id)
    _require_writable(db, definition, ctx)
    update_data = body.model_dump(exclude_unset=True)
    if "options" in update_data:
        _enforce_options_payload_rule(definition.type, update_data["options"])
        if definition.type in SELECT_TYPES:
            _guard_options_change(db, definition, update_data)
    if update_data.get("required") and definition.entity_type in REQUIRES_DEFAULT_ENTITY_TYPES:
        new_default = update_data.get("default_value", definition.default_value)
        if new_default is None:
            raise HTTPException(
                status_code=422,
                detail="required custom fields on executions or test cases must have a default_value",
            )
    for field, value in update_data.items():
        setattr(definition, field, value)
    db.commit()
    db.refresh(definition)
    return definition


@custom_fields_router.delete(
    "/{id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_custom_field(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    definition = _get_definition(db, id)
    _require_writable(db, definition, ctx)
    if _is_definition_in_use(db, definition):
        raise HTTPException(
            status_code=409,
            detail="Custom field has values on existing rows. Archive it instead.",
        )
    db.delete(definition)
    db.commit()


@custom_fields_router.post(
    "/{id}/archive", response_model=CustomFieldDefinitionOut
)
def archive_custom_field(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    definition = _get_definition(db, id)
    _require_writable(db, definition, ctx)
    if definition.archived_at is None:
        definition.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(definition)
    return definition


@custom_fields_router.post(
    "/{id}/unarchive", response_model=CustomFieldDefinitionOut
)
def unarchive_custom_field(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    definition = _get_definition(db, id)
    _require_writable(db, definition, ctx)
    definition.archived_at = None
    db.commit()
    db.refresh(definition)
    return definition


def _get_definition(db: Session, definition_id: int) -> CustomFieldDefinition:
    definition = db.get(CustomFieldDefinition, definition_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Not found")
    return definition


def _require_writable(
    db: Session, definition: CustomFieldDefinition, ctx: AuthContext
) -> None:
    if ctx.project_scope is not None and ctx.project_scope != definition.project_id:
        raise HTTPException(
            status_code=403, detail="API token is not authorized for this project"
        )
    require_project_writer(db, ctx.user, definition.project_id)
    project = db.get(Project, definition.project_id)
    if project is not None and project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")


def _enforce_options_payload_rule(
    field_type: str, options: list[dict] | None
) -> None:
    if field_type in SELECT_TYPES:
        if not options:
            raise HTTPException(
                status_code=422,
                detail=f"options required for type '{field_type}'",
            )
    elif options:
        raise HTTPException(
            status_code=422,
            detail=f"options not allowed for type '{field_type}'",
        )


ENTITY_TABLE: dict[str, str] = {
    "bug": "bugs",
    "test_case": "test_cases",
    "execution": "test_executions",
}


def _guard_options_change(
    db: Session,
    definition: CustomFieldDefinition,
    update_data: dict,
) -> None:
    """Refuse option edits that orphan existing values or invalidate the default.

    Admins routinely curate option lists after the fact, but two failure
    modes are silent today:

    * Removing an option that is still referenced from rows leaves those
      values as ghosts — the UI cannot re-select them and a PUT that
      omits ``custom_fields`` drops them entirely.
    * Replacing the option set without revisiting ``default_value`` makes
      future create calls explode with a 422 the user can't act on.

    We refuse both with a 409 / 422 that names the offending values so
    the admin can archive the field, migrate rows, or update the default
    before retrying.
    """
    new_options = update_data["options"] or []
    new_values = {option["value"] for option in new_options}
    old_values = {option["value"] for option in (definition.options or [])}
    removed = old_values - new_values
    if removed:
        in_use = _option_values_in_use(db, definition)
        blocking = sorted(removed & in_use)
        if blocking:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot remove option(s) {blocking}: still referenced "
                    f"by existing rows. Migrate the values or archive the "
                    f"field instead."
                ),
            )

    next_default = update_data.get("default_value", definition.default_value)
    if next_default is None:
        return
    if definition.type == "single_select" and next_default not in new_values:
        raise HTTPException(
            status_code=422,
            detail=(
                f"default_value '{next_default}' is not one of the new "
                f"options. Update or clear the default before changing options."
            ),
        )
    if definition.type == "multi_select":
        invalid = sorted(item for item in (next_default or []) if item not in new_values)
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"default_value entries {invalid} are not in the new "
                    f"options. Update or clear the default before changing options."
                ),
            )


def _option_values_in_use(
    db: Session, definition: CustomFieldDefinition
) -> set[str]:
    table = ENTITY_TABLE.get(definition.entity_type)
    if table is None:
        return set()
    rows = db.execute(text(f"SELECT custom_fields FROM {table}")).fetchall()
    seen: set[str] = set()
    for (raw,) in rows:
        if raw is None:
            continue
        data = raw if isinstance(raw, dict) else json.loads(raw)
        value = data.get(definition.key)
        if value is None:
            continue
        if isinstance(value, list):
            seen.update(item for item in value if isinstance(item, str))
        elif isinstance(value, str):
            seen.add(value)
    return seen


def _is_definition_in_use(db: Session, definition: CustomFieldDefinition) -> bool:
    table = ENTITY_TABLE.get(definition.entity_type)
    if table is None:
        return False
    dialect = db.bind.dialect.name if db.bind is not None else "postgresql"
    if dialect == "postgresql":
        sql = f"SELECT 1 FROM {table} WHERE custom_fields ? :key LIMIT 1"
    else:
        sql = (
            f"SELECT 1 FROM {table} "
            f"WHERE json_extract(custom_fields, :path) IS NOT NULL LIMIT 1"
        )
    params = (
        {"key": definition.key}
        if dialect == "postgresql"
        else {"path": f"$.{definition.key}"}
    )
    return db.execute(text(sql), params).first() is not None
