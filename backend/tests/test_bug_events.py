from testjam.services import bug_events


def test_deleted_broadcasts_to_project_and_bug_topics(monkeypatch):
    pushed: list = []
    monkeypatch.setattr(
        bug_events, "notify_project", lambda project_id, payload: pushed.append(("project", project_id, payload)),
    )
    monkeypatch.setattr(bug_events, "notify_bug", lambda bug_id, payload: pushed.append(("bug", bug_id, payload)))

    bug_events.on_bug_deleted(7, 21)

    payload = {"event": "bug.deleted", "data": {"id": 21}}
    assert pushed == [("project", 7, payload), ("bug", 21, payload)]
