"""WS broadcasts for test case comments.

Comments are scoped to a single case; subscribers join the ``case:{id}`` topic
to receive ``case.comment.added`` / ``.updated`` / ``.deleted`` events without
refetching the comment list.
"""
from __future__ import annotations

from typing import Any

from testjam.models.testcase import CaseComment
from testjam.realtime import notify_case
from testjam.schemas.testcase import CaseCommentOut


def _broadcast(case_id: int, event: str, data: dict[str, Any]) -> None:
    notify_case(case_id, {"event": event, "data": data})


def on_case_comment_added(comment: CaseComment) -> None:
    _broadcast(
        comment.test_case_id, "case.comment.added",
        CaseCommentOut.model_validate(comment).model_dump(mode="json"),
    )


def on_case_comment_updated(comment: CaseComment) -> None:
    _broadcast(
        comment.test_case_id, "case.comment.updated",
        CaseCommentOut.model_validate(comment).model_dump(mode="json"),
    )


def on_case_comment_deleted(case_id: int, comment_id: int) -> None:
    _broadcast(case_id, "case.comment.deleted", {"id": comment_id})
