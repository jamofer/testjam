"""Test-case attachment SDK coverage (upload / list / download / delete)."""
import io


def _seed_case(auth_client):
    project = auth_client.projects.find_or_create("Attach Project")
    suite = auth_client.suites.find_or_create(project["id"], "S")
    return auth_client.cases.find_or_create(suite["id"], "C")


def test_upload_and_list_attachment(auth_client):
    case = _seed_case(auth_client)

    uploaded = auth_client.cases.upload_attachment(
        case["id"], filename="spec.txt", content=io.BytesIO(b"hello"), mime="text/plain",
    )
    listing = auth_client.cases.list_attachments(case["id"])

    assert uploaded["filename"] == "spec.txt"
    assert [a["id"] for a in listing] == [uploaded["id"]]


def test_download_attachment_returns_bytes(auth_client):
    case = _seed_case(auth_client)
    uploaded = auth_client.cases.upload_attachment(
        case["id"], filename="binary.bin", content=io.BytesIO(b"\x00\x01\x02"),
        mime="application/octet-stream",
    )

    payload = auth_client.cases.download_attachment(case["id"], uploaded["id"])

    assert payload == b"\x00\x01\x02"


def test_delete_attachment_removes_row(auth_client):
    case = _seed_case(auth_client)
    uploaded = auth_client.cases.upload_attachment(
        case["id"], filename="gone.txt", content=io.BytesIO(b"bye"), mime="text/plain",
    )

    auth_client.cases.delete_attachment(case["id"], uploaded["id"])

    assert auth_client.cases.list_attachments(case["id"]) == []
