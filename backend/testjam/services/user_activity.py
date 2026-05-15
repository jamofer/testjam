from __future__ import annotations

from sqlalchemy.orm import Session

from testjam.models.execution import TestExecution
from testjam.models.project import Project
from testjam.models.testcase import TestCase, TestSuite
from testjam.models.user import User
from testjam.schemas.user import ActivityCase, ActivityExecution, UserActivity

ACTIVITY_LIMIT = 10


def collect_user_activity(db: Session, user: User) -> UserActivity:
    return UserActivity(
        last_login_at=user.last_login_at,
        last_login_ip=user.last_login_ip,
        recent_executions=_recent_executions(db, user.id),
        recent_cases=_recent_cases(db, user.id),
    )


def _recent_executions(db: Session, user_id: int) -> list[ActivityExecution]:
    rows = (
        db.query(TestExecution, Project.name)
        .join(Project, Project.id == TestExecution.project_id)
        .filter(TestExecution.created_by_id == user_id)
        .order_by(TestExecution.created_at.desc())
        .limit(ACTIVITY_LIMIT)
        .all()
    )
    return [
        ActivityExecution(
            id=execution.id,
            project_id=execution.project_id,
            project_name=project_name,
            title=execution.title,
            status=execution.status,
            created_at=execution.created_at,
        )
        for execution, project_name in rows
    ]


def _recent_cases(db: Session, user_id: int) -> list[ActivityCase]:
    rows = (
        db.query(TestCase, TestSuite.project_id, Project.name)
        .join(TestSuite, TestSuite.id == TestCase.suite_id)
        .join(Project, Project.id == TestSuite.project_id)
        .filter(TestCase.created_by_id == user_id)
        .order_by(TestCase.created_at.desc())
        .limit(ACTIVITY_LIMIT)
        .all()
    )
    return [
        ActivityCase(
            id=case.id,
            project_id=project_id,
            project_name=project_name,
            name=case.name,
            created_at=case.created_at,
        )
        for case, project_id, project_name in rows
    ]
