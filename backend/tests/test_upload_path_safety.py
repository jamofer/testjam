"""Upload endpoints sanitize the user-supplied filename.

A path-traversal filename must not write outside the per-resource
upload directory, and the persisted metadata must store the sanitized
name (not the raw client value).
"""
import os

import pytest

from testjam.services.uploads import safe_filename, safe_join, unique_path


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("../etc/passwd", "passwd"),
        ("../../etc/passwd", "passwd"),
        ("./.hidden", "hidden"),
        ("C:\\Windows\\System32\\notepad.exe", "notepad.exe"),
        ("/absolute/leak.bin", "leak.bin"),
        ("", "attachment"),
        (None, "attachment"),
        ("...", "attachment"),
        ("plain.txt", "plain.txt"),
    ],
)
def test_safe_filename(raw, expected):
    assert safe_filename(raw) == expected


def test_safe_join_keeps_destination_inside_directory(tmp_path):
    target_directory = str(tmp_path)
    destination = safe_join(target_directory, "../../escape.bin")

    assert destination.startswith(os.path.realpath(target_directory) + os.sep)
    assert destination.endswith("escape.bin")


def _seed_bug(client, project_id):
    response = client.post(
        f"/api/v1/projects/{project_id}/bugs",
        json={"title": "with attach"},
    )
    return response.json()


def test_bug_attachment_upload_strips_traversal(auth_client, project_id):
    bug = _seed_bug(auth_client, project_id)
    files = {"file": ("../../etc/secret.bin", b"x", "application/octet-stream")}

    response = auth_client.post(f"/api/v1/bugs/{bug['id']}/attachments", files=files)

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "secret.bin"


def test_unique_path_keeps_destination_inside_directory(tmp_path):
    target_directory = str(tmp_path)

    destination = unique_path(target_directory, "../../escape.bin")

    assert os.path.dirname(destination) == os.path.realpath(target_directory)


def test_unique_path_differs_for_the_same_filename(tmp_path):
    first = unique_path(str(tmp_path), "report.png")

    second = unique_path(str(tmp_path), "report.png")

    assert first != second


def test_same_filename_does_not_overwrite_earlier_case_attachment(auth_client, case_ids):
    case_id = case_ids[0]
    first = auth_client.post(
        f"/api/v1/cases/{case_id}/attachments", files={"file": ("log.txt", b"first", "text/plain")},
    ).json()
    auth_client.post(
        f"/api/v1/cases/{case_id}/attachments", files={"file": ("log.txt", b"second", "text/plain")},
    )

    response = auth_client.get(f"/api/v1/cases/{case_id}/attachments/{first['id']}/download")

    assert response.content == b"first"

