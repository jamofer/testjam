"""Catalog lookups and auto-create hooks for project environments.

The `TestExecution.environment` column remains a free string column so the
Robot Framework listener and JUnit importer don't break on legacy payloads.
This module provides:

- `slugify_environment`: deterministic normalization from arbitrary user text
  to a slug stored both in the catalog row and on `TestExecution.environment`.
- `resolve_environment`: lookup against the catalog for badge/color display.
- `upsert_from_execution`: called from execution-creating endpoints to add a
  catalog entry for a newly seen slug, gated by `AppSettings.auto_create_environments`.
- `apply_default_state`: keeps `is_default` mutually exclusive within a project.
"""
from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from testjam.models.environment import ProjectEnvironment
from testjam.models.settings import AppSettings


_SLUG_INVALID = re.compile(r"[^a-z0-9-]+")
_SLUG_COLLAPSE = re.compile(r"-{2,}")


def slugify_environment(raw: str) -> str:
    if not raw:
        return ""
    text = raw.strip().lower().replace("_", "-").replace(" ", "-")
    text = _SLUG_INVALID.sub("-", text)
    text = _SLUG_COLLAPSE.sub("-", text).strip("-")
    return text[:64]


def resolve_environment(
    db: Session, project_id: int, raw: str | None
) -> ProjectEnvironment | None:
    if not raw:
        return None
    slug = slugify_environment(raw)
    if not slug:
        return None
    return (
        db.query(ProjectEnvironment)
        .filter(
            ProjectEnvironment.project_id == project_id,
            ProjectEnvironment.slug == slug,
        )
        .first()
    )


def next_order(db: Session, project_id: int) -> int:
    current_max = db.scalar(
        select(func.coalesce(func.max(ProjectEnvironment.order), 0)).where(
            ProjectEnvironment.project_id == project_id
        )
    )
    return (current_max or 0) + 1


def apply_default_state(
    db: Session, project_id: int, target: ProjectEnvironment, make_default: bool
) -> None:
    if not make_default:
        target.is_default = False
        return
    db.query(ProjectEnvironment).filter(
        ProjectEnvironment.project_id == project_id,
        ProjectEnvironment.id != target.id,
        ProjectEnvironment.is_default.is_(True),
    ).update({ProjectEnvironment.is_default: False}, synchronize_session=False)
    target.is_default = True


def upsert_from_execution(
    db: Session, project_id: int, raw: str | None
) -> str | None:
    """Normalize `raw` to a slug; auto-create catalog entry if enabled.

    Returns the normalized slug (or None if `raw` is empty). Callers should
    use the returned value when persisting `TestExecution.environment`.
    """
    if not raw:
        return None
    slug = slugify_environment(raw)
    if not slug:
        return None
    existing = (
        db.query(ProjectEnvironment.id)
        .filter(
            ProjectEnvironment.project_id == project_id,
            ProjectEnvironment.slug == slug,
        )
        .first()
    )
    if existing is not None:
        return slug
    app_settings = db.get(AppSettings, 1)
    if app_settings is None or not app_settings.auto_create_environments:
        return slug
    db.add(
        ProjectEnvironment(
            project_id=project_id,
            name=raw.strip()[:64] or slug,
            slug=slug,
            order=next_order(db, project_id),
        )
    )
    db.flush()
    return slug
