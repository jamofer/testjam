"""HTML bug-report mention resolution must batch.

Each `@user` / `#bug` / `~case` / `!exec` chip in a report previously
triggered a per-occurrence call to `mention_resolver.resolve`, which
issues at least one SELECT per mention. A report with N bugs each
mentioning a handful of users would hit the DB ``N × mentions × pages``
times. The renderer now pre-resolves unique tokens once per report and
serves chips from an in-memory cache.

Strategy: render two reports against the same project, one with a few
mentions and one with many, and assert that the query count stays
bounded by the *unique* token count rather than the *occurrence* count.
"""
from sqlalchemy import event

from testjam.auth.security import hash_password
from testjam.models.bug import Bug, BugComment
from testjam.models.user import User
from tests.conftest import TestingSession, engine


def _seed_users(count):
    ids = []
    with TestingSession() as db:
        for i in range(count):
            user = User(
                username=f"mention-author-{i}",
                email=f"mention-author-{i}@x.com",
                hashed_password=hash_password("pw"),
                is_active=True,
            )
            db.add(user)
            db.flush()
            ids.append(user.id)
        db.commit()
    return ids


def _seed_bug_with_mentions(project_id, number, author_id, mentioned_username, comment_count):
    with TestingSession() as db:
        bug = Bug(
            project_id=project_id,
            number=number,
            title=f"Bug {number}",
            description=f"Reported by @{mentioned_username}. See #{number}.",
            severity="medium",
            status="open",
            created_by_id=author_id,
            updated_by_id=author_id,
        )
        db.add(bug)
        db.flush()
        for i in range(comment_count):
            db.add(BugComment(
                bug_id=bug.id,
                body=f"Cross-ref @{mentioned_username} again — {i}",
                created_by_id=author_id,
            ))
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


def test_html_report_resolves_each_unique_mention_once(auth_client, project_id):
    [author_id, mentioned_id] = _seed_users(2)
    mentioned_username = "mention-author-1"

    _seed_bug_with_mentions(project_id, 1, author_id, mentioned_username, comment_count=10)
    few_occurrences = _count_select_queries(
        lambda: auth_client.get(f"/api/v1/projects/{project_id}/bugs/report?format=html"),
    )

    for number in range(2, 12):
        _seed_bug_with_mentions(project_id, number, author_id, mentioned_username, comment_count=10)
    many_occurrences = _count_select_queries(
        lambda: auth_client.get(f"/api/v1/projects/{project_id}/bugs/report?format=html"),
    )

    extra_bugs = 10
    fan_out_budget = 12
    growth = many_occurrences - few_occurrences
    assert growth <= extra_bugs + fan_out_budget, (
        f"report mention resolution N+1: {few_occurrences} queries for 1 bug "
        f"(11 mentions), {many_occurrences} for 11 bugs (121 mentions); "
        f"growth {growth} > {extra_bugs + fan_out_budget}"
    )
