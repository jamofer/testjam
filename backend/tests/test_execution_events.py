"""execution_events service — lifecycle hooks dispatching email + WS."""
from __future__ import annotations

from collections.abc import Sequence

import pytest
from fastapi import BackgroundTasks

from testjam.auth.security import hash_password
from testjam.models.execution import TestExecution, TestResult
from testjam.models.notification import Notification
from testjam.models.project import Project
from testjam.models.settings import AppSettings
from testjam.models.user import User
from testjam.services import execution_events, notification_preferences
from tests.conftest import TestingSession


@pytest.fixture(autouse=True)
def stub_websocket_broadcasts(monkeypatch):
    monkeypatch.setattr(execution_events, "notify_project", lambda *a, **kw: None)
    monkeypatch.setattr(execution_events, "notify_execution", lambda *a, **kw: None)


@pytest.fixture
def smtp_configured():
    with TestingSession() as session:
        row = session.get(AppSettings, 1) or AppSettings(id=1)
        row.smtp_host = "smtp.example.com"
        row.smtp_from = "noreply@example.com"
        row.site_url = "https://qa.example.com"
        row.app_name = "Testjam"
        session.add(row)
        session.commit()


@pytest.fixture
def background():
    return BackgroundTasks()


@pytest.fixture
def make_user():
    def _make(username: str) -> int:
        with TestingSession() as session:
            user = User(
                username=username,
                email=f"{username}@example.com",
                hashed_password=hash_password("pw"),
                is_active=True,
            )
            session.add(user)
            session.commit()
            return user.id
    return _make


@pytest.fixture
def project_id():
    with TestingSession() as session:
        project = Project(name="P")
        session.add(project)
        session.commit()
        return project.id


@pytest.fixture
def make_execution(project_id):
    def _make(
        *,
        created_by_id: int | None = None,
        assigned_to_id: int | None = None,
        status: str = "in_progress",
        results: Sequence[str] = (),
    ) -> int:
        with TestingSession() as session:
            execution = TestExecution(
                project_id=project_id,
                title="Run",
                type="manual",
                status=status,
                created_by_id=created_by_id,
                assigned_to_id=assigned_to_id,
            )
            session.add(execution)
            session.flush()
            for offset, status_value in enumerate(results):
                session.add(TestResult(
                    execution_id=execution.id,
                    test_case_id=10_000 + offset,
                    status=status_value,
                ))
            session.commit()
            return execution.id
    return _make


def notifications_for(user_id: int) -> list[str]:
    with TestingSession() as session:
        rows = (
            session.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.id)
            .all()
        )
        return [row.type for row in rows]


def emails_in(background: BackgroundTasks) -> list:
    return [task for task in background.tasks if task.func.__name__ == "send_email"]


def call_on_completed(execution_id: int, background: BackgroundTasks) -> None:
    with TestingSession() as session:
        execution = session.get(TestExecution, execution_id)
        execution_events.on_execution_completed(session, execution, background)
        session.commit()


def test_completed_notifies_creator_when_no_assignee(
    smtp_configured, background, make_user, make_execution,
):
    creator_id = make_user("creator")
    execution_id = make_execution(
        created_by_id=creator_id, status="completed", results=("passed",),
    )

    call_on_completed(execution_id, background)

    assert notifications_for(creator_id) == ["execution_finished"]


def test_completed_notifies_creator_and_assignee_when_distinct(
    smtp_configured, background, make_user, make_execution,
):
    creator_id = make_user("creator")
    assignee_id = make_user("assignee")
    execution_id = make_execution(
        created_by_id=creator_id,
        assigned_to_id=assignee_id,
        status="completed",
        results=("passed",),
    )

    call_on_completed(execution_id, background)

    assert notifications_for(creator_id) == ["execution_finished"]
    assert notifications_for(assignee_id) == ["execution_finished"]


def test_completed_does_not_duplicate_when_assignee_is_creator(
    smtp_configured, background, make_user, make_execution,
):
    creator_id = make_user("solo")
    execution_id = make_execution(
        created_by_id=creator_id,
        assigned_to_id=creator_id,
        status="completed",
        results=("passed",),
    )

    call_on_completed(execution_id, background)

    assert notifications_for(creator_id) == ["execution_finished"]


def test_completed_with_failures_also_emits_failed_event(
    smtp_configured, background, make_user, make_execution,
):
    creator_id = make_user("creator")
    execution_id = make_execution(
        created_by_id=creator_id,
        status="completed",
        results=("passed", "failed"),
    )

    call_on_completed(execution_id, background)

    assert notifications_for(creator_id) == ["execution_finished", "execution_failed"]


def test_failed_event_schedules_email_with_default_preferences(
    smtp_configured, background, make_user, make_execution,
):
    creator_id = make_user("creator")
    execution_id = make_execution(
        created_by_id=creator_id,
        status="completed",
        results=("failed",),
    )

    call_on_completed(execution_id, background)

    assert len(emails_in(background)) == 1


def test_finished_event_does_not_schedule_email_with_default_preferences(
    smtp_configured, background, make_user, make_execution,
):
    creator_id = make_user("creator")
    execution_id = make_execution(
        created_by_id=creator_id,
        status="completed",
        results=("passed",),
    )

    call_on_completed(execution_id, background)

    assert emails_in(background) == []


def test_completed_skips_email_when_user_disabled_it(
    smtp_configured, background, make_user, make_execution,
):
    creator_id = make_user("creator")
    execution_id = make_execution(
        created_by_id=creator_id, status="completed", results=("failed",),
    )
    with TestingSession() as session:
        notification_preferences.set_preference(
            session, creator_id, "execution_failed", in_app=True, email=False,
        )

    call_on_completed(execution_id, background)

    assert notifications_for(creator_id) == ["execution_finished", "execution_failed"]
    assert emails_in(background) == []


def test_updated_does_not_call_completed_when_already_completed(
    monkeypatch, smtp_configured, background, make_user, make_execution,
):
    actor_id = make_user("actor")
    execution_id = make_execution(status="completed")
    calls: list = []
    monkeypatch.setattr(
        execution_events,
        "on_execution_completed",
        lambda db, execution, bg: calls.append(execution.id),
    )

    with TestingSession() as session:
        actor = session.get(User, actor_id)
        execution = session.get(TestExecution, execution_id)
        execution_events.on_execution_updated(
            session, execution, actor, background,
            previous_status="completed",
            previous_assignee_id=execution.assigned_to_id,
        )

    assert calls == []


def test_updated_triggers_completed_on_first_completion(
    monkeypatch, smtp_configured, background, make_user, make_execution,
):
    actor_id = make_user("actor")
    execution_id = make_execution(status="completed")
    calls: list = []
    monkeypatch.setattr(
        execution_events,
        "on_execution_completed",
        lambda db, execution, bg: calls.append(execution.id),
    )

    with TestingSession() as session:
        actor = session.get(User, actor_id)
        execution = session.get(TestExecution, execution_id)
        execution_events.on_execution_updated(
            session, execution, actor, background,
            previous_status="in_progress",
            previous_assignee_id=execution.assigned_to_id,
        )

    assert calls == [execution_id]


def test_updated_emits_assignment_email_when_assignee_changes(
    smtp_configured, background, make_user, make_execution,
):
    actor_id = make_user("actor")
    new_assignee_id = make_user("assignee")
    execution_id = make_execution(assigned_to_id=new_assignee_id)

    with TestingSession() as session:
        actor = session.get(User, actor_id)
        execution = session.get(TestExecution, execution_id)
        execution_events.on_execution_updated(
            session, execution, actor, background,
            previous_status="in_progress",
            previous_assignee_id=None,
        )
        session.commit()

    assert notifications_for(new_assignee_id) == ["execution_assigned"]
    assert len(emails_in(background)) == 1


def test_assigning_to_self_is_a_noop(
    smtp_configured, background, make_user, make_execution,
):
    actor_id = make_user("alice")
    execution_id = make_execution()

    with TestingSession() as session:
        actor = session.get(User, actor_id)
        execution = session.get(TestExecution, execution_id)
        execution_events.on_execution_assigned(
            session, execution, actor_id, actor, background,
        )
        session.commit()

    assert notifications_for(actor_id) == []
    assert emails_in(background) == []


def test_deleted_broadcasts_only(monkeypatch):
    pushed: list = []
    monkeypatch.setattr(
        execution_events,
        "notify_project",
        lambda project_id, payload: pushed.append((project_id, payload)),
    )

    execution_events.on_execution_deleted(42, 7)

    assert pushed == [(7, {
        "event": "execution.deleted",
        "data": {"id": 42, "project_id": 7},
    })]


def test_result_updated_broadcasts_to_execution_topic(monkeypatch):
    captured: list = []
    monkeypatch.setattr(
        execution_events,
        "notify_execution",
        lambda execution_id, payload: captured.append((execution_id, payload)),
    )

    execution_events.on_result_updated(11, {"id": 1, "status": "passed"})

    assert captured == [(11, {
        "event": "result.updated",
        "data": {"id": 1, "status": "passed"},
    })]


def test_step_result_finished_broadcasts_to_execution_topic(monkeypatch):
    captured: list = []
    monkeypatch.setattr(
        execution_events,
        "notify_execution",
        lambda execution_id, payload: captured.append((execution_id, payload)),
    )

    execution_events.on_step_result_finished(99, {"id": 1, "status": "passed"})

    assert captured == [(99, {
        "event": "step_result.finished",
        "data": {"id": 1, "status": "passed"},
    })]
