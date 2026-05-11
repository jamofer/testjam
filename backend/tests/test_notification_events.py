"""P3.7.1 — single source of truth for notification event-type strings."""

from testjam.services.notification_events import KNOWN_EVENT_TYPES, NotificationEvent


def test_event_values_are_stable_strings():
    """String values are persisted in DB; renames break existing rows."""
    assert NotificationEvent.EXECUTION_ASSIGNED == "execution_assigned"
    assert NotificationEvent.EXECUTION_FINISHED == "execution_finished"
    assert NotificationEvent.EXECUTION_FAILED == "execution_failed"
    assert NotificationEvent.MENTION_IN_COMMENT == "mention_in_comment"
    assert NotificationEvent.PASSWORD_RESET == "password_reset"
    assert NotificationEvent.ACCOUNT_INVITE == "account_invite"


def test_known_event_types_matches_enum():
    assert KNOWN_EVENT_TYPES == {e.value for e in NotificationEvent}


def test_event_str_round_trip():
    """StrEnum members must compare equal to plain strings (used in DB filters)."""
    assert NotificationEvent("execution_assigned") is NotificationEvent.EXECUTION_ASSIGNED
    assert str(NotificationEvent.EXECUTION_ASSIGNED) == "execution_assigned"


def test_no_duplicate_values():
    values = [e.value for e in NotificationEvent]
    assert len(values) == len(set(values))
