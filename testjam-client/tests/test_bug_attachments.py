"""Bug attachment SDK coverage (upload / list / download / delete)."""
import io


def _seed_bug(auth_client):
    project = auth_client.projects.find_or_create("Attach Bug Project")
    return auth_client.bugs.create(
        project["id"], title="Attach me", severity="medium",
    )


def test_upload_and_list_attachment(auth_client):
    bug = _seed_bug(auth_client)

    uploaded = auth_client.bugs.upload_attachment(
        bug["id"], filename="crash.log", content=io.BytesIO(b"trace"), mime="text/plain",
    )
    listing = auth_client.bugs.list_attachments(bug["id"])

    assert uploaded["filename"] == "crash.log"
    assert [row["id"] for row in listing] == [uploaded["id"]]


def test_download_attachment_returns_bytes(auth_client):
    bug = _seed_bug(auth_client)
    uploaded = auth_client.bugs.upload_attachment(
        bug["id"], filename="evidence.bin", content=io.BytesIO(b"\x00\x01\x02"),
        mime="application/octet-stream",
    )

    payload = auth_client.bugs.download_attachment(bug["id"], uploaded["id"])

    assert payload == b"\x00\x01\x02"


def test_delete_attachment_removes_row(auth_client):
    bug = _seed_bug(auth_client)
    uploaded = auth_client.bugs.upload_attachment(
        bug["id"], filename="gone.txt", content=io.BytesIO(b"bye"), mime="text/plain",
    )

    auth_client.bugs.delete_attachment(bug["id"], uploaded["id"])

    assert auth_client.bugs.list_attachments(bug["id"]) == []
