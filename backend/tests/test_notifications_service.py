"""`services.notifications.notify` dispatcher behavior."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import BackgroundTasks

from testjam.auth.security import hash_password
from testjam.models.notification import Notification
from testjam.models.settings import AppSettings
from testjam.models.user import User
from testjam.services import notification_preferences, notifications as notifications_module
from testjam.services.notification_events import NotificationEvent
from testjam.services.notifications import DEDUPE_WINDOW_SECONDS, notify
from tests.conftest import TestingSession


def _make_user(email: str | None = "alice@example.com") -> int:
    with TestingSession() as db:
        u = User(username="alice", email=email or "noemail@example.com",
                 hashed_password=hash_password("pw"), is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id


def _set_smtp(configured: bool):
    with TestingSession() as db:
        s = db.get(AppSettings, 1)
        if not s:
            s = AppSettings(id=1)
            db.add(s)
        if configured:
            s.smtp_host = "smtp.example.com"
            s.smtp_from = "noreply@example.com"
        else:
            s.smtp_host = None
            s.smtp_from = None
        db.commit()


@pytest.fixture
def captured_ws_pushes(monkeypatch):
    pushes: list[tuple[int, dict]] = []

    def fake_ws(user_id, payload):
        pushes.append((user_id, payload))

    monkeypatch.setattr(notifications_module, "ws_notify_user", fake_ws)
    return pushes


def test_persists_notification_row_and_pushes_ws(captured_ws_pushes):
    user_id = _make_user()
    bg = BackgroundTasks()

    with TestingSession() as db:
        n = notify(
            db, user_id, NotificationEvent.EXECUTION_ASSIGNED,
            message="hi", link="/x", background=bg,
        )
        db.commit()
        notif_id = n.id

    with TestingSession() as db:
        row = db.get(Notification, notif_id)
        assert row is not None
        assert row.type == "execution_assigned"
        assert row.message == "hi"
        assert row.link == "/x"
        assert row.user_id == user_id

    assert len(captured_ws_pushes) == 1
    pushed_user_id, payload = captured_ws_pushes[0]
    assert pushed_user_id == user_id
    assert payload["event"] == "notification"
    assert payload["data"]["type"] == "execution_assigned"


def test_no_email_when_smtp_unconfigured(captured_ws_pushes):
    user_id = _make_user()
    _set_smtp(False)
    bg = BackgroundTasks()

    with TestingSession() as db:
        notify(
            db, user_id, NotificationEvent.EXECUTION_ASSIGNED,
            message="hi", link="/x",
            email_subject="S", email_html="<p>h</p>", email_text="t",
            background=bg,
        )
        db.commit()

    assert bg.tasks == []


def test_no_email_when_email_args_missing(captured_ws_pushes):
    user_id = _make_user()
    _set_smtp(True)
    bg = BackgroundTasks()

    with TestingSession() as db:
        notify(
            db, user_id, NotificationEvent.EXECUTION_ASSIGNED,
            message="hi", link="/x", background=bg,
        )
        db.commit()

    assert bg.tasks == []


def test_no_email_when_background_is_none(captured_ws_pushes):
    user_id = _make_user()
    _set_smtp(True)

    with TestingSession() as db:
        notify(
            db, user_id, NotificationEvent.EXECUTION_ASSIGNED,
            message="hi", link="/x",
            email_subject="S", email_html="<p>h</p>",
            background=None,
        )
        db.commit()
    # Nothing to assert beyond "didn't crash"; background.add_task wasn't an option.


def test_schedules_email_task_when_configured(captured_ws_pushes):
    user_id = _make_user(email="alice@example.com")
    _set_smtp(True)
    bg = BackgroundTasks()

    with TestingSession() as db:
        notify(
            db, user_id, NotificationEvent.EXECUTION_ASSIGNED,
            message="hi", link="/x",
            email_subject="Subj", email_html="<p>h</p>", email_text="t",
            background=bg,
        )
        db.commit()

    assert len(bg.tasks) == 1
    task = bg.tasks[0]
    # FastAPI BackgroundTask stores positional args and the callable
    assert task.func.__name__ == "send_email"
    # send_email(settings, to, subject, html, text)
    assert task.args[1] == "alice@example.com"
    assert task.args[2] == "Subj"
    assert task.args[3] == "<p>h</p>"
    assert task.args[4] == "t"


def test_skips_email_when_user_has_no_email(captured_ws_pushes):
    """User without email should still get DB+WS notif but no email."""
    user_id = _make_user(email=None)
    # Force email column to empty after creation (DB requires non-null)
    with TestingSession() as db:
        u = db.get(User, user_id)
        u.email = ""
        db.commit()
    _set_smtp(True)
    bg = BackgroundTasks()

    with TestingSession() as db:
        notify(
            db, user_id, NotificationEvent.EXECUTION_ASSIGNED,
            message="hi", link="/x",
            email_subject="S", email_html="<p>h</p>",
            background=bg,
        )
        db.commit()

    assert bg.tasks == []


def _send(user_id, event_type, link, background, **email_kwargs):
    with TestingSession() as db:
        result = notify(
            db, user_id, event_type,
            message=email_kwargs.pop("message", "msg"),
            link=link,
            background=background,
            **email_kwargs,
        )
        db.commit()
        return result


def _count_notifications(user_id):
    with TestingSession() as db:
        return db.query(Notification).filter(Notification.user_id == user_id).count()


def _backdate_notification(user_id, seconds_ago):
    backdated = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=seconds_ago)
    with TestingSession() as db:
        row = db.query(Notification).filter(Notification.user_id == user_id).one()
        row.created_at = backdated
        db.commit()


def test_dedupes_consecutive_calls_with_same_user_type_link(captured_ws_pushes):
    user_id = _make_user()
    _set_smtp(True)
    bg = BackgroundTasks()
    email = dict(email_subject="S", email_html="<p>h</p>", email_text="t")

    first = _send(user_id, NotificationEvent.EXECUTION_ASSIGNED, "/executions/9/run", bg, **email)
    second = _send(user_id, NotificationEvent.EXECUTION_ASSIGNED, "/executions/9/run", bg, **email)

    assert first is not None
    assert second is None
    assert _count_notifications(user_id) == 1
    assert len(captured_ws_pushes) == 1
    assert len(bg.tasks) == 1


def test_does_not_dedupe_when_link_differs(captured_ws_pushes):
    user_id = _make_user()
    bg = BackgroundTasks()

    _send(user_id, NotificationEvent.EXECUTION_ASSIGNED, "/executions/1/run", bg)
    _send(user_id, NotificationEvent.EXECUTION_ASSIGNED, "/executions/2/run", bg)

    assert _count_notifications(user_id) == 2


def test_does_not_dedupe_when_event_type_differs(captured_ws_pushes):
    user_id = _make_user()
    bg = BackgroundTasks()

    _send(user_id, NotificationEvent.EXECUTION_FINISHED, "/executions/9", bg)
    _send(user_id, NotificationEvent.EXECUTION_FAILED, "/executions/9", bg)

    assert _count_notifications(user_id) == 2


def test_resends_after_dedupe_window_expires(captured_ws_pushes):
    user_id = _make_user()
    bg = BackgroundTasks()

    _send(user_id, NotificationEvent.EXECUTION_ASSIGNED, "/executions/9/run", bg)
    _backdate_notification(user_id, DEDUPE_WINDOW_SECONDS + 1)
    second = _send(user_id, NotificationEvent.EXECUTION_ASSIGNED, "/executions/9/run", bg)

    assert second is not None
    assert _count_notifications(user_id) == 2


def _set_email_pref(user_id, event_type, *, in_app=True, email=True):
    with TestingSession() as db:
        notification_preferences.set_preference(
            db, user_id, str(event_type), in_app=in_app, email=email,
        )


def test_keeps_in_app_and_ws_when_email_pref_is_disabled(captured_ws_pushes):
    user_id = _make_user()
    _set_smtp(True)
    _set_email_pref(user_id, NotificationEvent.EXECUTION_ASSIGNED, email=False)
    bg = BackgroundTasks()

    _send(
        user_id, NotificationEvent.EXECUTION_ASSIGNED, "/x", bg,
        email_subject="S", email_html="<p>h</p>", email_text="t",
    )

    assert _count_notifications(user_id) == 1
    assert len(captured_ws_pushes) == 1
    assert bg.tasks == []


def test_skips_in_app_and_ws_when_in_app_pref_is_disabled(captured_ws_pushes):
    user_id = _make_user()
    _set_smtp(True)
    _set_email_pref(user_id, NotificationEvent.EXECUTION_ASSIGNED, in_app=False, email=True)
    bg = BackgroundTasks()

    result = _send(
        user_id, NotificationEvent.EXECUTION_ASSIGNED, "/x", bg,
        email_subject="S", email_html="<p>h</p>", email_text="t",
    )

    assert result is None
    assert _count_notifications(user_id) == 0
    assert captured_ws_pushes == []
    assert len(bg.tasks) == 1
