"""Helpers for capturing TestCase definition snapshots into case_revisions."""
from __future__ import annotations

from sqlalchemy.orm import Session

from testjam.models.case_revision import CaseRevision
from testjam.models.testcase import TestCase
from testjam.models.user import User


def write_revision(db: Session, case: TestCase, actor: User | None, kind: str) -> CaseRevision | None:
    """Insert a CaseRevision row for this case unless the snapshot is unchanged.

    Returns the existing latest revision (without inserting) when the case
    definition matches the previously-stored snapshot. Caller commits.
    """
    snapshot = case_snapshot(case)
    latest = _latest_revision(db, case.id)
    if latest is not None and latest.snapshot == snapshot:
        return latest

    rev = CaseRevision(
        case_id=case.id,
        change_kind=kind,
        actor_id=actor.id if actor else None,
        snapshot=snapshot,
    )
    db.add(rev)
    return rev


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


def _latest_revision(db: Session, case_id: int) -> CaseRevision | None:
    return (
        db.query(CaseRevision)
        .filter(CaseRevision.case_id == case_id)
        .order_by(CaseRevision.created_at.desc(), CaseRevision.id.desc())
        .first()
    )
