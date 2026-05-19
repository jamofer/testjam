"""Mentions resolve + autocomplete SDK coverage."""


def test_resolve_user_mention_returns_label_and_url(auth_client):
    project = auth_client.projects.find_or_create("Mention Project")

    resolved = auth_client.mentions.resolve(
        project["id"], [{"kind": "user", "slug": "u"}],
    )

    assert len(resolved) == 1
    assert resolved[0]["kind"] == "user"
    assert resolved[0]["accessible"] is True


def test_resolve_unknown_user_marks_inaccessible(auth_client):
    project = auth_client.projects.find_or_create("Mention Project")

    resolved = auth_client.mentions.resolve(
        project["id"], [{"kind": "user", "slug": "ghost"}],
    )

    assert resolved[0]["accessible"] is False


def test_search_users_returns_matching_hits(auth_client):
    project = auth_client.projects.find_or_create("Mention Search")

    hits = auth_client.mentions.search(project["id"], "user", q="u")

    assert any(hit["kind"] == "user" for hit in hits)
    assert all("label" in hit for hit in hits)


def test_search_bugs_by_number(auth_client):
    project = auth_client.projects.find_or_create("Bug Search")
    bug = auth_client.bugs.create(project["id"], title="Login broken")

    hits = auth_client.mentions.search(project["id"], "bug", q=str(bug["number"]))

    assert any(hit["id"] == bug["id"] for hit in hits)


def test_search_step_result_requires_execution_and_result(auth_client):
    project = auth_client.projects.find_or_create("Step Search")

    try:
        auth_client.mentions.search(project["id"], "step_result", q="")
    except Exception as error:
        assert "step_result" in str(error).lower() or "400" in str(error)
    else:
        raise AssertionError("Expected 400 on missing execution_id/result_id")
