"""Public-report share tokens SDK coverage."""


def _seed_project_with_bug(auth_client):
    project = auth_client.projects.find_or_create("PublicReportProj")
    auth_client.bugs.create(project["id"], title="Login broken", severity="high")
    return project


def test_create_returns_raw_token(auth_client):
    project = _seed_project_with_bug(auth_client)

    share = auth_client.public_reports.create(
        project["id"], kind="bug_report", label="Sprint 7",
    )

    assert share["kind"] == "bug_report"
    assert share["token"]
    assert share["url_path"].endswith(share["token"])


def test_list_omits_raw_token(auth_client):
    project = _seed_project_with_bug(auth_client)
    auth_client.public_reports.create(project["id"], kind="bug_report")

    listing = auth_client.public_reports.list(project["id"])

    assert len(listing) == 1
    assert "token" not in listing[0]


def test_revoke_marks_as_revoked(auth_client):
    project = _seed_project_with_bug(auth_client)
    share = auth_client.public_reports.create(project["id"], kind="bug_report")

    auth_client.public_reports.revoke(project["id"], share["id"])

    listing = auth_client.public_reports.list(project["id"])
    assert listing[0]["revoked_at"] is not None


def test_fetch_html_renders_bugs_anonymously(auth_client):
    project = _seed_project_with_bug(auth_client)
    share = auth_client.public_reports.create(project["id"], kind="bug_report")

    html = auth_client.public_reports.fetch_html(share["token"])

    assert "Login broken" in html
