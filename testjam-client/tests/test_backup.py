"""Backup download via the SDK.

Hits the real `/settings/backup` endpoint through the in-process FastAPI
transport. SQLite mode is used in tests so the path exercises
`_sqlite_dump_to`, not `pg_dump`.
"""
from __future__ import annotations

import io
import json
import zipfile


def test_download_bytes_returns_a_valid_zip(auth_client):
    payload = auth_client.backup.download_bytes()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "dump.sql" in names
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["format_version"] == 1


def test_download_writes_archive_to_explicit_path(auth_client, tmp_path):
    target = tmp_path / "snapshots" / "instance.zip"

    written = auth_client.backup.download(target)

    assert written == target
    assert target.exists()
    assert target.stat().st_size > 0
    with zipfile.ZipFile(target) as archive:
        assert "manifest.json" in archive.namelist()


def test_download_into_directory_uses_content_disposition_filename(auth_client, tmp_path):
    destination = tmp_path / "backups"
    destination.mkdir()

    written = auth_client.backup.download(destination)

    assert written.parent == destination
    assert written.name.startswith("testjam-backup-")
    assert written.name.endswith(".zip")
