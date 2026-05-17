"""Bug tracking endpoints.

Two routers mounted under `/api/v1`:

- `/projects/{id}/bugs` — list, create, report, lookup-by-number.
- `/bugs/{id}` and nested — detail, update, delete, status, comments,
  attachments, history.

Permissions:

- Create / comment / change status: any project member with role >= tester.
- Delete bug: project owner or admin.
- Delete own comment: author. Delete any comment: project owner or admin.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from testjam.auth.dependencies import (
    AuthContext,
    get_auth_context,
    get_current_user,
    require_project_access,
    require_writable_project_access,
)
from testjam.database import get_db
from testjam.models.bug import Bug, BugActivity, BugAttachment, BugComment, BugLink
from testjam.models.execution import TestExecution
from testjam.models.project import Project
from testjam.models.user import User
from testjam.schemas.bug import (
    BugActivityOut,
    BugAttachmentOut,
    BugCommentCreate,
    BugCommentOut,
    BugCommentUpdate,
    BugContextOut,
    BugCreate,
    BugLinkCreate,
    BugLinkOut,
    BugOut,
    BugStatusChange,
    BugUpdate,
    RECIPROCAL_LINK_KIND,
    TERMINAL_BUG_STATUSES,
)
from fastapi.responses import HTMLResponse, StreamingResponse

from testjam.services import bug_activity, bug_context, bug_events, bug_reports, mention_notify
from testjam.services.bug_numbering import next_bug_number
from testjam.services.environments import upsert_from_execution
from testjam.services.permissions import effective_role


def _bug_mention_subject(bug: Bug) -> str:
    return f"bug #{bug.number} {bug.title}"


def _bug_mention_link(bug: Bug) -> str:
    return f"/projects/{bug.project_id}/bugs/{bug.number}"


def _fan_out_mentions(
    db: Session,
    bug: Bug,
    body: str | None,
    previous_body: str | None,
    actor: User,
    background: BackgroundTasks,
) -> None:
    if not body:
        return
    mention_notify.notify_mentions(
        db,
        project_id=bug.project_id,
        body=body,
        previous_body=previous_body,
        subject_object=_bug_mention_subject(bug),
        link_path=_bug_mention_link(bug),
        actor=actor,
        background=background,
    )


WRITER_ROLES = {"tester", "owner"}
projects_router = APIRouter(prefix="/projects", tags=["Bugs"])
bugs_router = APIRouter(prefix="/bugs", tags=["Bugs"])


def _bug_out(bug: Bug) -> BugOut:
    return bug_events.bug_out(bug)


def _touch_updated_by(bug: Bug, current: User) -> None:
    bug.updated_by_id = current.id


def _can_write_project(db: Session, user: User, project_id: int) -> bool:
    if user.is_admin:
        return True
    return effective_role(db, user.id, project_id) in WRITER_ROLES


def _can_delete_project_resource(db: Session, user: User, project_id: int) -> bool:
    if user.is_admin:
        return True
    return effective_role(db, user.id, project_id) == "owner"


def _require_writer(db: Session, user: User, project_id: int) -> None:
    if not _can_write_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Tester role or higher required")


def _require_owner_or_admin(db: Session, user: User, project_id: int) -> None:
    if not _can_delete_project_resource(db, user, project_id):
        raise HTTPException(status_code=403, detail="Project owner or admin required")


def _ensure_project_writable(db: Session, project_id: int) -> None:
    project = db.get(Project, project_id)
    if project is not None and project.archived_at is not None:
        raise HTTPException(status_code=409, detail="Project is archived")


def _get_bug(db: Session, bug_id: int) -> Bug:
    bug = db.get(Bug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail="Not found")
    return bug


def _authorize_bug_access(ctx: AuthContext, bug: Bug) -> None:
    if ctx.project_scope is not None and ctx.project_scope != bug.project_id:
        raise HTTPException(
            status_code=403, detail="API token is not authorized for this project"
        )


def _resolve_environment_from_execution(
    db: Session, project_id: int, execution_id: int | None, fallback: str | None
) -> str | None:
    if fallback:
        return upsert_from_execution(db, project_id, fallback)
    if execution_id is None:
        return None
    execution = db.get(TestExecution, execution_id)
    return execution.environment if execution else None


@projects_router.get("/{id}/bugs", response_model=list[BugOut])
def list_bugs(
    id: int,
    status: str | None = None,
    severity: str | None = None,
    version_id: int | None = None,
    fixed_in_version_id: int | None = None,
    assigned_to_id: int | None = None,
    tag: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    limit = min(limit, 200)
    query = db.query(Bug).filter(Bug.project_id == id)
    if status:
        query = query.filter(Bug.status == status)
    if severity:
        query = query.filter(Bug.severity == severity)
    if version_id is not None:
        query = query.filter(Bug.version_id == version_id)
    if fixed_in_version_id is not None:
        query = query.filter(Bug.fixed_in_version_id == fixed_in_version_id)
    if assigned_to_id is not None:
        query = query.filter(Bug.assigned_to_id == assigned_to_id)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(func.lower(Bug.title).like(like))
    rows = query.order_by(Bug.number.desc()).offset(skip).limit(limit).all()
    if tag:
        rows = [bug for bug in rows if bug.tags and tag in bug.tags]
    return [_bug_out(bug) for bug in rows]


@projects_router.post(
    "/{id}/bugs", response_model=BugOut, status_code=status.HTTP_201_CREATED
)
def create_bug(
    id: int,
    body: BugCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    _require_writer(db, current, id)
    _ensure_project_writable(db, id)

    payload = body.model_dump()
    environment = _resolve_environment_from_execution(
        db, id, payload.get("execution_id"), payload.get("environment"),
    )
    bug = Bug(
        project_id=id,
        number=next_bug_number(db, id),
        title=payload["title"],
        description=payload.get("description"),
        severity=payload.get("severity", "medium"),
        status="open",
        tags=payload.get("tags") or None,
        result_id=payload.get("result_id"),
        execution_id=payload.get("execution_id"),
        version_id=payload.get("version_id"),
        environment=environment,
        assigned_to_id=payload.get("assigned_to_id"),
        fixed_in_version_id=payload.get("fixed_in_version_id"),
        created_by_id=current.id,
        updated_by_id=current.id,
    )
    for attempt in range(5):
        try:
            db.add(bug)
            db.flush()
            break
        except IntegrityError:
            db.rollback()
            bug.number = next_bug_number(db, id)
    else:
        raise HTTPException(status_code=409, detail="Could not allocate bug number")

    bug_activity.record_status_change(db, bug.id, None, "open", current.id)
    db.commit()
    db.refresh(bug)
    bug_events.on_bug_created(db, bug, current, background)
    _fan_out_mentions(db, bug, bug.description, None, current, background)
    return _bug_out(bug)


@projects_router.get("/{id}/bugs/by-number/{number}", response_model=BugOut)
def get_bug_by_number(
    id: int,
    number: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_project_access),
):
    bug = db.query(Bug).filter(Bug.project_id == id, Bug.number == number).first()
    if bug is None:
        raise HTTPException(status_code=404, detail="Not found")
    return _bug_out(bug)


@bugs_router.get("/{id}", response_model=BugOut)
def get_bug(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return _bug_out(bug)


@bugs_router.put("/{id}", response_model=BugOut)
def update_bug(
    id: int,
    body: BugUpdate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_writer(db, current, bug.project_id)
    _ensure_project_writable(db, bug.project_id)

    update_data = body.model_dump(exclude_unset=True)
    previous_assignee_id = bug.assigned_to_id
    previous_snapshot = bug_activity.snapshot(bug)
    previous_description = bug.description
    if "environment" in update_data and update_data["environment"]:
        update_data["environment"] = upsert_from_execution(
            db, bug.project_id, update_data["environment"],
        )
    for field, value in update_data.items():
        setattr(bug, field, value)
    _touch_updated_by(bug, current)
    db.commit()
    db.refresh(bug)
    if "assigned_to_id" in update_data and bug.assigned_to_id != previous_assignee_id:
        bug_events.on_bug_assigned(db, bug, previous_assignee_id, current, background)
    bug_events.on_bug_updated(db, bug, previous_snapshot, current)
    if "description" in update_data:
        _fan_out_mentions(db, bug, bug.description, previous_description, current, background)
    return _bug_out(bug)


@bugs_router.post("/{id}/status", response_model=BugOut)
def change_bug_status(
    id: int,
    body: BugStatusChange,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_writer(db, current, bug.project_id)
    _ensure_project_writable(db, bug.project_id)

    previous_status = bug.status
    bug.status = body.status
    if body.status in TERMINAL_BUG_STATUSES and bug.resolved_at is None:
        bug.resolved_at = datetime.now(timezone.utc)
    elif body.status not in TERMINAL_BUG_STATUSES:
        bug.resolved_at = None
    activity_row = bug_activity.record_status_change(
        db, bug.id, previous_status, body.status, current.id, body.note,
    )
    _touch_updated_by(bug, current)
    db.commit()
    db.refresh(bug)
    db.refresh(activity_row)
    bug_events.on_bug_status_changed(db, bug, activity_row, current, background)
    return _bug_out(bug)


@bugs_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bug(
    id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_owner_or_admin(db, current, bug.project_id)
    project_id = bug.project_id
    bug_id = bug.id
    db.delete(bug)
    db.commit()
    bug_events.on_bug_deleted(project_id, bug_id)


@bugs_router.get("/{id}/comments", response_model=list[BugCommentOut])
def list_comments(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return list(bug.comments)


@bugs_router.post(
    "/{id}/comments", response_model=BugCommentOut, status_code=status.HTTP_201_CREATED
)
def add_comment(
    id: int,
    body: BugCommentCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_writer(db, current, bug.project_id)
    _ensure_project_writable(db, bug.project_id)
    comment = BugComment(bug_id=bug.id, body=body.body, created_by_id=current.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    bug_events.on_bug_comment_added(comment)
    _fan_out_mentions(db, bug, comment.body, None, current, background)
    return comment


@bugs_router.put("/{id}/comments/{comment_id}", response_model=BugCommentOut)
def update_comment(
    id: int,
    comment_id: int,
    body: BugCommentUpdate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    comment = db.get(BugComment, comment_id)
    if comment is None or comment.bug_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    if comment.created_by_id != current.id and not current.is_admin:
        raise HTTPException(status_code=403, detail="Only the author or admin can edit")
    previous_body = comment.body
    comment.body = body.body
    db.commit()
    db.refresh(comment)
    bug_events.on_bug_comment_updated(comment)
    _fan_out_mentions(db, comment.bug, comment.body, previous_body, current, background)
    return comment


@bugs_router.delete("/{id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    comment = db.get(BugComment, comment_id)
    if comment is None or comment.bug_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    bug = comment.bug
    is_author = comment.created_by_id == current.id
    if not is_author and not _can_delete_project_resource(db, current, bug.project_id):
        raise HTTPException(status_code=403, detail="Only the author or project owner can delete")
    db.delete(comment)
    db.commit()
    bug_events.on_bug_comment_deleted(bug.id, comment_id)


@bugs_router.get("/{id}/context", response_model=BugContextOut)
def get_bug_context(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return bug_context.build_bug_context(db, bug)


@bugs_router.get("/{id}/links", response_model=list[BugLinkOut])
def list_links(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return [bug_events.link_out(link, db) for link in bug.links]


@bugs_router.post(
    "/{id}/links", response_model=BugLinkOut, status_code=status.HTTP_201_CREATED
)
def add_link(
    id: int,
    body: BugLinkCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    bug = _get_bug(db, id)
    _require_writer(db, current, bug.project_id)
    _ensure_project_writable(db, bug.project_id)

    if body.target_bug_id is not None:
        target = db.get(Bug, body.target_bug_id)
        if target is None or target.project_id != bug.project_id:
            raise HTTPException(status_code=404, detail="Target bug not found")

    link = BugLink(
        bug_id=bug.id,
        kind=body.kind,
        label=body.label,
        url=body.url,
        execution_id=body.execution_id,
        test_case_id=body.test_case_id,
        test_step_id=body.test_step_id,
        target_bug_id=body.target_bug_id,
        created_by_id=current.id,
    )
    db.add(link)

    if body.kind is not None and body.target_bug_id is not None:
        reciprocal = BugLink(
            bug_id=body.target_bug_id,
            kind=RECIPROCAL_LINK_KIND[body.kind],
            target_bug_id=bug.id,
            label=body.label,
            created_by_id=current.id,
        )
        db.add(reciprocal)

    _touch_updated_by(bug, current)
    db.commit()
    db.refresh(link)
    bug_events.on_bug_link_added(link, db)
    link_activity = bug_activity.record_link_added(db, bug.id, link, current.id)
    db.commit()
    bug_events.on_bug_activity_recorded(db, link_activity)
    if body.kind is not None and body.target_bug_id is not None:
        target_bug = db.get(Bug, body.target_bug_id)
        if target_bug is not None:
            _touch_updated_by(target_bug, current)
            db.commit()
        bug_events.on_bug_link_added(reciprocal, db)
        reciprocal_activity = bug_activity.record_link_added(
            db, reciprocal.bug_id, reciprocal, current.id,
        )
        db.commit()
        bug_events.on_bug_activity_recorded(db, reciprocal_activity)
    return bug_events.link_out(link, db)


@bugs_router.delete("/{id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    id: int,
    link_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    link = db.get(BugLink, link_id)
    if link is None or link.bug_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    bug = link.bug
    is_author = link.created_by_id == current.id
    if not is_author and not _can_delete_project_resource(db, current, bug.project_id):
        raise HTTPException(status_code=403, detail="Only the author or project owner can delete")

    reciprocal = _find_reciprocal_link(db, link)
    link_activity = bug_activity.record_link_deleted(db, bug.id, link, current.id)
    reciprocal_activity = (
        bug_activity.record_link_deleted(db, reciprocal.bug_id, reciprocal, current.id)
        if reciprocal is not None else None
    )
    db.delete(link)
    if reciprocal is not None:
        db.delete(reciprocal)
    _touch_updated_by(bug, current)
    db.commit()
    bug_events.on_bug_link_deleted(bug.id, link_id)
    bug_events.on_bug_activity_recorded(db, link_activity)
    if reciprocal is not None and reciprocal_activity is not None:
        bug_events.on_bug_link_deleted(reciprocal_activity.bug_id, reciprocal.id)
        bug_events.on_bug_activity_recorded(db, reciprocal_activity)


def _find_reciprocal_link(db: Session, link: BugLink) -> BugLink | None:
    if link.kind is None or link.target_bug_id is None:
        return None
    expected_kind = RECIPROCAL_LINK_KIND.get(link.kind)
    if expected_kind is None:
        return None
    return (
        db.query(BugLink)
        .filter(
            BugLink.bug_id == link.target_bug_id,
            BugLink.target_bug_id == link.bug_id,
            BugLink.kind == expected_kind,
        )
        .first()
    )


@bugs_router.get("/{id}/activity", response_model=list[BugActivityOut])
def list_activity(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return list(bug.activity)


@bugs_router.get("/{id}/attachments", response_model=list[BugAttachmentOut])
def list_attachments(
    id: int,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(get_auth_context),
):
    bug = _get_bug(db, id)
    _authorize_bug_access(ctx, bug)
    return list(bug.attachments)


@projects_router.get("/{id}/bugs/report")
def download_bug_report(
    id: int,
    format: str = "html",
    version_id: int | None = None,
    environment: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(require_project_access),
):
    project = db.get(Project, id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if format == "xlsx":
        payload = bug_reports.render_xlsx(db, project, current, version_id, environment)
        return StreamingResponse(
            iter([payload]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="bugs-{project.name}.xlsx"'},
        )
    if format != "html":
        raise HTTPException(status_code=400, detail="format must be 'html' or 'xlsx'")
    html = bug_reports.render_html(db, project, current, version_id, environment)
    return HTMLResponse(content=html)
