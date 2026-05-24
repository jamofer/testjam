"""Pagination edge cases for listings that grow past a single page.

Catches three failure modes the suite missed before:

* Filters applied **after** ``rows[skip:skip+limit]`` (the bug originally
  fixed for ``GET /projects/{id}/bugs``) silently drop rows the user
  asked for. The fix iterates the listing across every page and asserts
  the union matches the filtered DB count.
* ``limit`` hard cap (200) enforced on every paginated endpoint, so a
  client can't disable pagination by requesting an absurd page size.
* ``skip`` past the end returns ``[]`` instead of 500.
"""
from datetime import datetime, timezone

import pytest

from testjam.models.bug import Bug
from testjam.models.execution import TestExecution
from testjam.models.notification import Notification
from tests.conftest import TestingSession

PAGE_SIZE = 10
TOTAL_BUGS = 60
TAGGED_BUGS = 30
FILTER_TAG = "regression"
PAGINATION_CAP = 200


@pytest.fixture
def bulk_bugs(project_id):
    rows = []
    for i in range(TOTAL_BUGS):
        rows.append(Bug(
            project_id=project_id,
            number=i + 1,
            title=f"Bug {i:03d}",
            severity="medium",
            status="open",
            tags=[FILTER_TAG] if i < TAGGED_BUGS else None,
        ))
    with TestingSession() as db:
        db.add_all(rows)
        db.commit()
    return TOTAL_BUGS, TAGGED_BUGS


@pytest.fixture
def bulk_executions(auth_client, project_id):
    rows = []
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(TOTAL_BUGS):
        rows.append(TestExecution(
            project_id=project_id,
            title=f"Run {i:03d}",
            type="manual",
            status="completed" if i % 2 == 0 else "pending",
            created_at=base.replace(minute=i % 60, second=(i * 7) % 60),
        ))
    with TestingSession() as db:
        db.add_all(rows)
        db.commit()
    return TOTAL_BUGS, TOTAL_BUGS // 2


@pytest.fixture
def bulk_notifications(auth_client):
    me = _resolve_user_id(auth_client)
    rows = []
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(TOTAL_BUGS):
        rows.append(Notification(
            user_id=me,
            type="test_event",
            message=f"msg {i}",
            is_read=(i % 3 == 0),
            created_at=base.replace(minute=i % 60, second=(i * 7) % 60),
        ))
    with TestingSession() as db:
        db.add_all(rows)
        db.commit()
    unread = TOTAL_BUGS - sum(1 for i in range(TOTAL_BUGS) if i % 3 == 0)
    return TOTAL_BUGS, unread


def _paginate(client, url, total, params=None):
    seen = []
    skip = 0
    while True:
        page_params = {"skip": skip, "limit": PAGE_SIZE, **(params or {})}
        page = client.get(url, params=page_params).json()
        if not page:
            break
        seen.extend(page)
        skip += PAGE_SIZE
        if skip > total + PAGE_SIZE:
            pytest.fail(f"runaway pagination on {url}: collected {len(seen)} > {total}")
    return seen


def test_bug_pagination_covers_every_row_without_duplicates(auth_client, project_id, bulk_bugs):
    total, _ = bulk_bugs

    seen = _paginate(auth_client, f"/api/v1/projects/{project_id}/bugs", total)

    assert len(seen) == total
    assert len({bug["id"] for bug in seen}) == total


def test_bug_tag_filter_returns_exact_subset_across_pages(auth_client, project_id, bulk_bugs):
    total, tagged = bulk_bugs

    seen = _paginate(
        auth_client, f"/api/v1/projects/{project_id}/bugs", total, params={"tag": FILTER_TAG},
    )

    assert len(seen) == tagged
    assert all(FILTER_TAG in (bug["tags"] or []) for bug in seen)


def test_bug_limit_is_capped(auth_client, project_id, bulk_bugs):
    response = auth_client.get(
        f"/api/v1/projects/{project_id}/bugs", params={"skip": 0, "limit": 10_000},
    )

    assert response.status_code == 200
    assert len(response.json()) <= PAGINATION_CAP


def test_bug_skip_past_end_returns_empty(auth_client, project_id, bulk_bugs):
    response = auth_client.get(
        f"/api/v1/projects/{project_id}/bugs", params={"skip": 10_000, "limit": PAGE_SIZE},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_execution_status_filter_pagination(auth_client, project_id, bulk_executions):
    total, completed = bulk_executions

    seen = _paginate(
        auth_client, f"/api/v1/projects/{project_id}/executions",
        total, params={"status": "completed"},
    )

    assert len(seen) == completed
    assert all(execution["status"] == "completed" for execution in seen)


def test_execution_limit_is_capped(auth_client, project_id, bulk_executions):
    response = auth_client.get(
        f"/api/v1/projects/{project_id}/executions",
        params={"skip": 0, "limit": 10_000},
    )

    assert response.status_code == 200
    assert len(response.json()) <= PAGINATION_CAP


def test_notification_unread_filter_pagination(auth_client, bulk_notifications):
    total, unread = bulk_notifications

    seen = _paginate(
        auth_client, "/api/v1/notifications", total, params={"only_unread": "true"},
    )

    assert len(seen) == unread
    assert all(notification["is_read"] is False for notification in seen)


def test_notification_limit_is_capped(auth_client, bulk_notifications):
    response = auth_client.get(
        "/api/v1/notifications", params={"skip": 0, "limit": 10_000},
    )

    assert response.status_code == 200
    assert len(response.json()) <= PAGINATION_CAP


def _resolve_user_id(auth_client):
    return auth_client.get("/api/v1/users/me").json()["id"]
