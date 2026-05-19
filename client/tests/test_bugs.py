"""Bug tracking SDK coverage."""


def _seed_bug(auth_client):
    project = auth_client.projects.find_or_create("BugProj")
    bug = auth_client.bugs.create(
        project["id"],
        title="Login crash",
        description="Form throws on submit",
        severity="high",
        tags=["regression"],
    )
    return project, bug


def test_create_and_list_bugs(auth_client):
    project, bug = _seed_bug(auth_client)

    assert bug["number"] == 1
    assert bug["severity"] == "high"

    listing = auth_client.bugs.list(project["id"])
    assert [b["id"] for b in listing] == [bug["id"]]


def test_filter_bugs_by_severity(auth_client):
    project, _ = _seed_bug(auth_client)
    auth_client.bugs.create(project["id"], title="Typo", severity="low")

    high_only = auth_client.bugs.list(project["id"], severity="high")
    low_only = auth_client.bugs.list(project["id"], severity="low")

    assert {b["severity"] for b in high_only} == {"high"}
    assert {b["severity"] for b in low_only} == {"low"}


def test_get_by_number(auth_client):
    project, bug = _seed_bug(auth_client)

    fetched = auth_client.bugs.get_by_number(project["id"], bug["number"])

    assert fetched["id"] == bug["id"]


def test_update_bug(auth_client):
    _, bug = _seed_bug(auth_client)

    updated = auth_client.bugs.update(bug["id"], title="Renamed", severity="critical")

    assert updated["title"] == "Renamed"
    assert updated["severity"] == "critical"


def test_change_status_marks_resolved_at(auth_client):
    _, bug = _seed_bug(auth_client)

    resolved = auth_client.bugs.change_status(bug["id"], "resolved", note="fixed")

    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None


def test_comments_lifecycle(auth_client):
    _, bug = _seed_bug(auth_client)

    comment = auth_client.bugs.add_comment(bug["id"], "Repro confirmed")
    auth_client.bugs.update_comment(bug["id"], comment["id"], "Repro confirmed on dev")
    comments = auth_client.bugs.list_comments(bug["id"])

    assert len(comments) == 1
    assert comments[0]["body"] == "Repro confirmed on dev"

    auth_client.bugs.delete_comment(bug["id"], comment["id"])
    assert auth_client.bugs.list_comments(bug["id"]) == []


def test_watch_unwatch(auth_client):
    _, bug = _seed_bug(auth_client)

    watched = auth_client.bugs.watch(bug["id"])
    assert watched["watcher_count"] == 1
    watchers = auth_client.bugs.list_watchers(bug["id"])
    assert len(watchers) == 1

    unwatched = auth_client.bugs.unwatch(bug["id"])
    assert unwatched["watcher_count"] == 0


def test_links_and_activity(auth_client):
    project, bug = _seed_bug(auth_client)
    other = auth_client.bugs.create(project["id"], title="Dup")

    link = auth_client.bugs.add_link(
        bug["id"], kind="duplicate_of", target_bug_id=other["id"],
    )
    links = auth_client.bugs.list_links(bug["id"])
    activity = auth_client.bugs.list_activity(bug["id"])

    assert link["target_bug_id"] == other["id"]
    assert len(links) == 1
    assert any(a["field"] == "link" for a in activity)

    auth_client.bugs.delete_link(bug["id"], link["id"])
    assert auth_client.bugs.list_links(bug["id"]) == []


def test_attachments_empty_by_default(auth_client):
    _, bug = _seed_bug(auth_client)

    assert auth_client.bugs.list_attachments(bug["id"]) == []


def test_context_endpoint(auth_client):
    _, bug = _seed_bug(auth_client)

    ctx = auth_client.bugs.context(bug["id"])

    assert "execution" in ctx
    assert ctx["execution"] is None


def test_download_html_report(auth_client):
    project, _ = _seed_bug(auth_client)

    payload = auth_client.bugs.download_report(project["id"], format="html")

    assert payload.startswith(b"<")


def test_delete_bug(auth_client):
    project, bug = _seed_bug(auth_client)

    auth_client.bugs.delete(bug["id"])

    assert auth_client.bugs.list(project["id"]) == []
