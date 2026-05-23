"""Listener should not rewrite a case's steps when they already match."""
from testjam_client.listener.listener import _steps_match


def _payload(actions: list[tuple[str, str]]) -> list[dict]:
    return [
        {"action": action, "step_type": step_type, "order": index + 1}
        for index, (action, step_type) in enumerate(actions)
    ]


def _existing(actions: list[tuple[str, str]]) -> list[dict]:
    return [
        {"id": 100 + index, "action": action, "step_type": step_type, "order": index + 1}
        for index, (action, step_type) in enumerate(actions)
    ]


def test_identical_sequence_matches():
    actions = [("Open Browser", "setup"), ("Click Login", "action"), ("Close", "teardown")]

    assert _steps_match(_existing(actions), _payload(actions)) is True


def test_different_length_does_not_match():
    existing = _existing([("Open", "setup"), ("Click", "action")])
    payload = _payload([("Open", "setup")])

    assert _steps_match(existing, payload) is False


def test_changed_action_does_not_match():
    existing = _existing([("Open", "setup"), ("Click", "action")])
    payload = _payload([("Open", "setup"), ("Renamed", "action")])

    assert _steps_match(existing, payload) is False


def test_changed_step_type_does_not_match():
    existing = _existing([("Open", "setup")])
    payload = _payload([("Open", "action")])

    assert _steps_match(existing, payload) is False


def test_reordered_action_does_not_match():
    existing = _existing([("First", "action"), ("Second", "action")])
    payload = _payload([("Second", "action"), ("First", "action")])

    assert _steps_match(existing, payload) is False


def test_existing_out_of_order_is_normalised_before_compare():
    out_of_order = [
        {"id": 2, "action": "Second", "step_type": "action", "order": 2},
        {"id": 1, "action": "First", "step_type": "action", "order": 1},
    ]
    payload = _payload([("First", "action"), ("Second", "action")])

    assert _steps_match(out_of_order, payload) is True


def test_missing_step_type_defaults_to_action():
    existing = [{"id": 1, "action": "Click", "order": 1}]
    payload = _payload([("Click", "action")])

    assert _steps_match(existing, payload) is True
