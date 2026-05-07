"""Helpers for capturing TestCase definition snapshots into case_revisions."""
from __future__ import annotations

from sqlalchemy.orm import Session

from testjam.models.case_revision import CaseRevision
from testjam.models.testcase import TestCase
from testjam.models.user import User


def case_snapshot(case: TestCase) -> dict:
    return {
        "name": case.name,
        "description": case.description,
        "preconditions": case.preconditions,
        "setup": case.setup,
        "teardown": case.teardown,
        "tags": list(case.tags or []),
        "external_id": case.external_id,
        "steps": [
            {
                "order": s.order,
                "step_type": s.step_type,
                "action": s.action,
                "expected_result": s.expected_result,
            }
            for s in sorted(case.steps or [], key=lambda x: x.order)
        ],
    }


def write_revision(db: Session, case: TestCase, actor: User | None, kind: str) -> CaseRevision:
    """Insert a CaseRevision row for this case. Caller commits."""
    rev = CaseRevision(
        case_id=case.id,
        change_kind=kind,
        actor_id=actor.id if actor else None,
        snapshot=case_snapshot(case),
    )
    db.add(rev)
    return rev
