from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from testjam.models.project import ProjectGroup, ProjectMember
from testjam.models.user import GroupMember

ROLE_PRIORITY: dict[str, int] = {"owner": 3, "tester": 2, "viewer": 1}
VALID_ROLES: set[str] = set(ROLE_PRIORITY.keys())
WRITER_ROLES: set[str] = {"owner", "tester"}
OWNER_ROLES: set[str] = {"owner"}


def has_project_access(db: Session, user, project_id: int) -> bool:
    if user.is_admin:
        return True
    return effective_role(db, user.id, project_id) is not None


def is_project_writer(db: Session, user, project_id: int) -> bool:
    if user.is_admin:
        return True
    return effective_role(db, user.id, project_id) in WRITER_ROLES


def effective_role(db: Session, user_id: int, project_id: int) -> str | None:
    direct = (
        db.query(ProjectMember.role)
        .filter(ProjectMember.user_id == user_id, ProjectMember.project_id == project_id)
        .scalar()
    )
    via_group = (
        db.query(ProjectGroup.role)
        .join(GroupMember, GroupMember.group_id == ProjectGroup.group_id)
        .filter(GroupMember.user_id == user_id, ProjectGroup.project_id == project_id)
        .all()
    )
    candidates = [role for role in [direct, *(row[0] for row in via_group)] if role in ROLE_PRIORITY]
    if not candidates:
        return None
    return max(candidates, key=lambda role: ROLE_PRIORITY[role])


def effective_roles(db: Session, project_id: int) -> dict[int, str]:
    """Every user with access to the project, direct or through a group, mapped to their highest role."""
    direct = db.query(ProjectMember.user_id, ProjectMember.role).filter(ProjectMember.project_id == project_id)
    via_group = (
        db.query(GroupMember.user_id, ProjectGroup.role)
        .join(ProjectGroup, ProjectGroup.group_id == GroupMember.group_id)
        .filter(ProjectGroup.project_id == project_id)
    )
    roles: dict[int, str] = {}
    for user_id, role in [*direct.all(), *via_group.all()]:
        if _outranks(role, roles.get(user_id)):
            roles[user_id] = role
    return roles


def accessible_project_ids(db: Session, user_id: int) -> set[int]:
    direct_ids = {
        row[0]
        for row in db.query(ProjectMember.project_id).filter(ProjectMember.user_id == user_id).all()
    }
    via_group_stmt = (
        select(ProjectGroup.project_id)
        .join(GroupMember, GroupMember.group_id == ProjectGroup.group_id)
        .where(GroupMember.user_id == user_id)
    )
    via_group_ids = {row[0] for row in db.execute(via_group_stmt).all()}
    return direct_ids | via_group_ids


def _outranks(role: str, current: str | None) -> bool:
    if role not in ROLE_PRIORITY:
        return False
    return current is None or ROLE_PRIORITY[role] > ROLE_PRIORITY[current]
