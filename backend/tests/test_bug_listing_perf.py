"""Bug-listing query count must stay constant as N grows.

Without `selectinload` on the three User relationships (`assigned_to`,
`created_by`, `updated_by`), `_bug_out` triggers a per-row lazy load — a
classic N+1. This test counts SELECTs across two list sizes and refuses
to let the count scale with the row count.
"""
from sqlalchemy import event

from testjam.auth.security import hash_password
from testjam.models.bug import Bug
from testjam.models.user import User
from tests.conftest import TestingSession, engine

SMALL_BUGS = 5
LARGE_BUGS = 25
QUERY_GROWTH_BUDGET = 5


def _seed_users(count):
    ids = []
    with TestingSession() as db:
        for i in range(count):
            user = User(
                username=f"author-{i}",
                email=f"author-{i}@x.com",
                hashed_password=hash_password("pw"),
                is_active=True,
            )
            db.add(user)
            db.flush()
            ids.append(user.id)
        db.commit()
    return ids


def _seed_bugs(project_id, count, user_ids, number_offset=0):
    with TestingSession() as db:
        rows = []
        for i in range(count):
            bug_index = number_offset + i
            rows.append(Bug(
                project_id=project_id,
                number=bug_index + 1,
                title=f"Bug {bug_index}",
                severity="medium",
                status="open",
                assigned_to_id=user_ids[bug_index * 3],
                created_by_id=user_ids[bug_index * 3 + 1],
                updated_by_id=user_ids[bug_index * 3 + 2],
            ))
        db.add_all(rows)
        db.commit()


def _count_select_queries(callable_):
    counter = {"n": 0}

    def listener(conn, cursor, statement, parameters, context, executemany):
        if statement.strip().upper().startswith("SELECT"):
            counter["n"] += 1

    event.listen(engine, "before_cursor_execute", listener)
    try:
        callable_()
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    return counter["n"]


def test_bug_listing_query_count_does_not_scale_with_row_count(auth_client, project_id):
    user_ids = _seed_users(LARGE_BUGS * 3)

    _seed_bugs(project_id, SMALL_BUGS, user_ids)
    small_queries = _count_select_queries(
        lambda: auth_client.get(f"/api/v1/projects/{project_id}/bugs"),
    )

    _seed_bugs(project_id, LARGE_BUGS - SMALL_BUGS, user_ids, number_offset=SMALL_BUGS)
    large_queries = _count_select_queries(
        lambda: auth_client.get(f"/api/v1/projects/{project_id}/bugs"),
    )

    growth = large_queries - small_queries
    assert growth <= QUERY_GROWTH_BUDGET, (
        f"bug listing N+1: {small_queries} queries for {SMALL_BUGS} bugs, "
        f"{large_queries} for {LARGE_BUGS} bugs (growth {growth} > {QUERY_GROWTH_BUDGET})"
    )
