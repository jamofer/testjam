"""CLI smoke for `testjam backup`.

Reuses the `auth_client` fixture (in-process FastAPI) and patches
`runtime.build_client` so the CLI talks to the same admin SDK instance.
"""
from __future__ import annotations

import zipfile

import pytest
from typer.testing import CliRunner

from testjam_client.cli import app

runner = CliRunner()


@pytest.fixture
def cli_admin(auth_client, tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TESTJAM_CONFIG", str(config_file))
    config_file.write_text('[profiles.default]\nurl = "http://testserver/api/v1"\n')
    monkeypatch.setattr(auth_client, "close", lambda: None)
    monkeypatch.setattr(
        "testjam_client.cli.runtime.build_client",
        lambda state: auth_client,
    )
    return auth_client


def test_backup_writes_archive_to_directory(cli_admin, tmp_path):
    target = tmp_path / "out"

    result = runner.invoke(app, ["--json", "backup", "--out", str(target)])

    assert result.exit_code == 0, result.output
    archives = list(target.glob("testjam-backup-*.zip"))
    assert len(archives) == 1
    with zipfile.ZipFile(archives[0]) as archive:
        assert "manifest.json" in archive.namelist()


def test_backup_writes_archive_to_explicit_file(cli_admin, tmp_path):
    target = tmp_path / "snapshot.zip"

    result = runner.invoke(app, ["--json", "backup", "--out", str(target)])

    assert result.exit_code == 0, result.output
    assert target.exists()
    with zipfile.ZipFile(target) as archive:
        assert "manifest.json" in archive.namelist()
