from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from testjam.models.execution import TestExecution
from testjam.models.project import Project, ProjectMember
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.user import User
from testjam.schemas.project import AdminProjectRow


def list_admin_projects(db: Session, include_archived: bool) -> list[AdminProjectRow]:
    query = db.query(Project)
    if not include_archived:
        query = query.filter(Project.archived_at.is_(None))
    projects = query.order_by(Project.name.asc()).all()
    if not projects:
        return []

    project_ids = [project.id for project in projects]
    owners = _owners_by_project(db, project_ids)
    members = _member_counts(db, project_ids)
    cases = _case_counts(db, project_ids)
    last_executions = _last_executions(db, project_ids)

    rows: list[AdminProjectRow] = []
    for project in projects:
        owner = owners.get(project.id)
        rows.append(AdminProjectRow(
            id=project.id,
            name=project.name,
            description=project.description,
            archived_at=project.archived_at,
            owner_id=owner[0] if owner else None,
            owner_username=owner[1] if owner else None,
            member_count=members.get(project.id, 0),
            case_count=cases.get(project.id, 0),
            last_execution_at=last_executions.get(project.id),
            created_at=project.created_at,
        ))
    return rows


def _owners_by_project(db: Session, project_ids: list[int]) -> dict[int, tuple[int, str]]:
    member = aliased(ProjectMember)
    rows = (
        db.query(member.project_id, User.id, User.username)
        .join(User, User.id == member.user_id)
        .filter(member.project_id.in_(project_ids), member.role == "owner")
        .all()
    )
    return {project_id: (user_id, username) for project_id, user_id, username in rows}


def _member_counts(db: Session, project_ids: list[int]) -> dict[int, int]:
    rows = (
        db.query(ProjectMember.project_id, func.count(ProjectMember.id))
        .filter(ProjectMember.project_id.in_(project_ids))
        .group_by(ProjectMember.project_id)
        .all()
    )
    return dict(rows)


def _case_counts(db: Session, project_ids: list[int]) -> dict[int, int]:
    rows = (
        db.query(TestSuite.project_id, func.count(TestCase.id))
        .join(TestCase, TestCase.suite_id == TestSuite.id)
        .filter(TestSuite.project_id.in_(project_ids))
        .group_by(TestSuite.project_id)
        .all()
    )
    return dict(rows)


def _last_executions(db: Session, project_ids: list[int]) -> dict[int, object]:
    rows = (
        db.query(TestExecution.project_id, func.max(TestExecution.created_at))
        .filter(TestExecution.project_id.in_(project_ids))
        .group_by(TestExecution.project_id)
        .all()
    )
    return dict(rows)
