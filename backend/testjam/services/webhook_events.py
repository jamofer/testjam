"""Single dispatch point for outbound webhook events.

Callers fire a generic ``fire_event`` that loads every active ``Webhook`` for
the project subscribed to the given event type and schedules one delivery per
match. Payload serialization is the caller's job — pass a plain dict that is
safe to ``json.dumps`` (use ``model.model_dump(mode="json")``).
"""
from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy import cast
from sqlalchemy.orm import Session

from testjam.models.webhook import Webhook
from testjam.services import webhook_dispatch


def fire_event(
    db: Session,
    project_id: int,
    event_type: str,
    payload: dict[str, Any],
    background: BackgroundTasks | None,
) -> int:
    webhooks = (
        db.query(Webhook)
        .filter(Webhook.project_id == project_id, Webhook.is_active == True)  # noqa: E712
        .all()
    )
    subscribed = [w for w in webhooks if event_type in (w.events or [])]
    if not subscribed:
        return 0
    envelope = webhook_dispatch.build_envelope(event_type, payload, project_id)
    for webhook in subscribed:
        webhook_dispatch.schedule_dispatch(background, webhook.id, event_type, envelope)
    return len(subscribed)
