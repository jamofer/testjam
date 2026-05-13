"""User soft-delete with owner-reassignment / project-archive resolution."""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from testjam.models.project import Project, ProjectMember
from testjam.models.user import User
from testjam.schemas.user import OwnedProjectAction, UnresolvedOwnedProject

OWNER_ROLE = "owner"


def soft_delete_user(
    db: Session,
    target: User,
    actions: list[OwnedProjectAction],
) -> None:
    """Soft-delete `target`, resolving any project they uniquely own first.

    Raises 409 if the caller did not provide a complete resolution plan.
    """
    unresolved = unresolved_owned_projects(db, target)
    by_id = {action.project_id: action for action in actions}
    missing = [project for project in unresolved if project.id not in by_id]
    if missing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "User uniquely owns projects; provide a resolution for each",
                "owned_projects": [_describe(db, project) for project in missing],
            },
        )

    for project in unresolved:
        action = by_id[project.id]
        _apply_action(db, project, target, action)

    db.query(ProjectMember).filter(ProjectMember.user_id == target.id).delete(
        synchronize_session=False,
    )
    target.deleted_at = datetime.now(timezone.utc)
    target.is_active = False
    db.commit()


def unresolved_owned_projects(db: Session, user: User) -> list[Project]:
    """Projects where `user` is the only owner — these must be resolved on delete."""
    owned_membership_rows = (
        db.query(ProjectMember)
        .filter(ProjectMember.user_id == user.id, ProjectMember.role == OWNER_ROLE)
        .all()
    )
    unique_owner_projects: list[Project] = []
    for membership in owned_membership_rows:
        other_owner_count = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == membership.project_id,
                ProjectMember.role == OWNER_ROLE,
                ProjectMember.user_id != user.id,
            )
            .count()
        )
        if other_owner_count == 0:
            project = db.get(Project, membership.project_id)
            if project is not None:
                unique_owner_projects.append(project)
    return unique_owner_projects


def _apply_action(
    db: Session,
    project: Project,
    target: User,
    action: OwnedProjectAction,
) -> None:
    if action.action == "archive":
        if project.archived_at is None:
            project.archived_at = datetime.now(timezone.utc)
        return

    if action.new_owner_id is None:
        raise HTTPException(
            status_code=400,
            detail=f"Project {project.id}: reassign requires new_owner_id",
        )
    if action.new_owner_id == target.id:
        raise HTTPException(
            status_code=400,
            detail=f"Project {project.id}: cannot reassign ownership to the user being deleted",
        )
    new_owner = db.get(User, action.new_owner_id)
    if new_owner is None or new_owner.deleted_at is not None or not new_owner.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Project {project.id}: new owner is not a valid active user",
        )
    existing = (
        db.query(ProjectMember)
        .filter_by(project_id=project.id, user_id=new_owner.id)
        .first()
    )
    if existing is not None:
        existing.role = OWNER_ROLE
    else:
        db.add(ProjectMember(project_id=project.id, user_id=new_owner.id, role=OWNER_ROLE))


def _describe(db: Session, project: Project) -> dict:
    candidate_ids = [
        membership.user_id
        for membership in db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id != _resolve_target_id(db, project),
        ).all()
    ]
    return UnresolvedOwnedProject(
        project_id=project.id,
        project_name=project.name,
        candidate_member_ids=candidate_ids,
    ).model_dump()


def _resolve_target_id(db: Session, project: Project) -> int:
    """Helper used by `_describe` only — returns the unique owner's user_id."""
    owner = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.role == OWNER_ROLE)
        .first()
    )
    return owner.user_id if owner else 0
