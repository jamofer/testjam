"""Replace the database and uploads tree from a backup archive.

The archive must contain `manifest.json`, `dump.sql`, and an `uploads/` tree
(produced by `services/backup.py`). Restore is destructive: existing tables
are dropped via the `--clean` statements in the dump and the uploads tree is
replaced wholesale.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from urllib.parse import urlparse

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine

from testjam.core.config import settings
from testjam.services.backup import (
    DUMP_FILENAME,
    MANIFEST_FILENAME,
)

SUPPORTED_FORMAT_VERSION = 1


class RestoreSummary(BaseModel):
    schema_revision: str | None
    dialect: str
    uploads_restored: int


def restore_backup(engine: Engine, archive_bytes: bytes) -> RestoreSummary:
    with tempfile.TemporaryDirectory(prefix="testjam-restore-") as workdir:
        archive_path = os.path.join(workdir, "backup.zip")
        with open(archive_path, "wb") as fh:
            fh.write(archive_bytes)

        try:
            with zipfile.ZipFile(archive_path) as zf:
                manifest = _read_manifest(zf)
                _validate_manifest(manifest, engine.dialect.name)
                zf.extractall(workdir)
        except zipfile.BadZipFile as e:
            raise HTTPException(status_code=400, detail="Invalid zip archive") from e

        dump_path = os.path.join(workdir, DUMP_FILENAME)
        if not os.path.isfile(dump_path):
            raise HTTPException(status_code=400, detail="Backup missing dump.sql")

        _apply_dump(engine, dump_path)
        uploads_count = _restore_uploads(os.path.join(workdir, "uploads"), settings.UPLOAD_DIR)

        return RestoreSummary(
            schema_revision=manifest.get("schema_revision"),
            dialect=manifest.get("dialect", "unknown"),
            uploads_restored=uploads_count,
        )


def _read_manifest(zf: zipfile.ZipFile) -> dict:
    try:
        with zf.open(MANIFEST_FILENAME) as fh:
            return json.loads(fh.read().decode("utf-8"))
    except KeyError as e:
        raise HTTPException(status_code=400, detail="Backup missing manifest.json") from e
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Backup manifest is not valid JSON") from e


def _validate_manifest(manifest: dict, current_dialect: str) -> None:
    fmt = manifest.get("format_version")
    if fmt != SUPPORTED_FORMAT_VERSION:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported backup format_version: {fmt}",
        )
    backup_dialect = manifest.get("dialect")
    if backup_dialect and backup_dialect != current_dialect:
        raise HTTPException(
            status_code=400,
            detail=f"Dialect mismatch: backup={backup_dialect} server={current_dialect}",
        )


def _apply_dump(engine: Engine, dump_path: str) -> None:
    if engine.dialect.name == "postgresql":
        _psql_apply(engine.url.render_as_string(hide_password=False), dump_path)
    else:
        _sqlite_apply(engine, dump_path)


def _psql_apply(database_url: str, dump_path: str) -> None:
    parsed = urlparse(database_url)
    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = parsed.password
    cmd = [
        "psql",
        "--quiet",
        "--single-transaction",
        "--set", "ON_ERROR_STOP=on",
        "--host", parsed.hostname or "localhost",
        "--port", str(parsed.port or 5432),
        "--username", parsed.username or "",
        "--dbname", (parsed.path or "/").lstrip("/"),
        "--file", dump_path,
    ]
    result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace")
        raise HTTPException(status_code=500, detail=f"psql restore failed: {stderr.strip()}")


def _sqlite_apply(engine: Engine, dump_path: str) -> None:
    with open(dump_path) as fh:
        script = fh.read()
    with engine.begin() as conn:
        for table in _list_user_tables(conn):
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
        raw = conn.connection
        raw.executescript(script)


def _list_user_tables(conn) -> list[str]:
    rows = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    ).all()
    return [row[0] for row in rows]


def _restore_uploads(source_dir: str, target_dir: str) -> int:
    if os.path.isdir(target_dir):
        for entry in os.listdir(target_dir):
            full = os.path.join(target_dir, entry)
            if os.path.isdir(full):
                shutil.rmtree(full, ignore_errors=True)
            else:
                try:
                    os.unlink(full)
                except FileNotFoundError:
                    pass
    os.makedirs(target_dir, exist_ok=True)

    if not os.path.isdir(source_dir):
        return 0

    count = 0
    for root, _, files in os.walk(source_dir):
        rel = os.path.relpath(root, source_dir)
        dest_root = target_dir if rel == "." else os.path.join(target_dir, rel)
        os.makedirs(dest_root, exist_ok=True)
        for name in files:
            shutil.copy2(os.path.join(root, name), os.path.join(dest_root, name))
            count += 1
    return count
