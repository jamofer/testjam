from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from testjam.models.project import ProjectGroup, ProjectMember
from testjam.models.user import GroupMember

ROLE_PRIORITY: dict[str, int] = {"owner": 3, "tester": 2, "viewer": 1}
VALID_ROLES: set[str] = set(ROLE_PRIORITY.keys())


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
