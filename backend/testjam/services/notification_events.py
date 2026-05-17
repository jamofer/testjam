"""Single source of truth for notification event-type strings.

Shared across:
- `Notification.type` rows in DB
- WS payloads (`{"event": "notification.<type>"}` and friends from P2.11)
- Email template lookup
- User notification preferences (P3.7.3)

Add new events HERE first, then plumb routers/templates/UI to consume them.
"""
from __future__ import annotations

from enum import StrEnum


class NotificationEvent(StrEnum):
    """All notification event types known to the backend.

    Values are the literal strings persisted in `notifications.type` and
    used as keys in user notification preferences.
    """

    EXECUTION_ASSIGNED = "execution_assigned"
    EXECUTION_FINISHED = "execution_finished"
    EXECUTION_FAILED = "execution_failed"

    BUG_ASSIGNED = "bug_assigned"
    BUG_RESOLVED = "bug_resolved"
    BUG_STATUS_CHANGED = "bug_status_changed"

    # Reserved for future work — not yet emitted.
    MENTION_IN_COMMENT = "mention_in_comment"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_INVITE = "account_invite"


KNOWN_EVENT_TYPES: frozenset[str] = frozenset(e.value for e in NotificationEvent)
