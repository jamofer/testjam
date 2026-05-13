"""Whole-instance backup: SQL dump + uploads directory + manifest.

Produces a single ZIP archive containing:
    manifest.json   — app version, schema revision, dialect, created_at
    dump.sql        — pg_dump output (Postgres) or iterdump() (SQLite)
    uploads/...     — verbatim copy of the uploads tree

The archive is written to a temp file and streamed back; the caller is
responsible for scheduling cleanup via BackgroundTasks.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import urlparse

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from testjam.core.config import settings

MANIFEST_FILENAME = "manifest.json"
DUMP_FILENAME = "dump.sql"
UPLOADS_PREFIX = "uploads/"


@dataclass
class BackupArtifact:
    path: str
    filename: str


def create_backup(db: Session, engine: Engine) -> BackupArtifact:
    dialect = engine.dialect.name
    dump_path = _dump_database(db, engine)
    manifest = _build_manifest(db, dialect)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fd, archive_path = tempfile.mkstemp(prefix=f"testjam-backup-{timestamp}-", suffix=".zip")
    os.close(fd)

    try:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(MANIFEST_FILENAME, json.dumps(manifest, indent=2))
            zf.write(dump_path, DUMP_FILENAME)
            _add_uploads_tree(zf, settings.UPLOAD_DIR)
    finally:
        _safe_unlink(dump_path)

    return BackupArtifact(path=archive_path, filename=f"testjam-backup-{timestamp}.zip")


def _build_manifest(db: Session, dialect: str) -> dict:
    return {
        "app_version": _app_version(),
        "schema_revision": _alembic_revision(db),
        "dialect": dialect,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "format_version": 1,
    }


def _dump_database(db: Session, engine: Engine) -> str:
    fd, dump_path = tempfile.mkstemp(prefix="testjam-dump-", suffix=".sql")
    os.close(fd)
    try:
        if engine.dialect.name == "postgresql":
            _pg_dump_to(engine.url.render_as_string(hide_password=False), dump_path)
        else:
            _sqlite_dump_to(db, dump_path)
        return dump_path
    except Exception:
        _safe_unlink(dump_path)
        raise


def _pg_dump_to(database_url: str, dump_path: str) -> None:
    parsed = urlparse(database_url)
    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = parsed.password
    cmd = [
        "pg_dump",
        "--clean", "--if-exists", "--no-owner", "--no-privileges",
        "--host", parsed.hostname or "localhost",
        "--port", str(parsed.port or 5432),
        "--username", parsed.username or "",
        "--dbname", (parsed.path or "/").lstrip("/"),
    ]
    with open(dump_path, "w") as out:
        result = subprocess.run(cmd, env=env, stdout=out, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr.decode('utf-8', 'replace')}")


def _sqlite_dump_to(db: Session, dump_path: str) -> None:
    raw = db.connection().connection
    with open(dump_path, "w") as out:
        for statement in raw.iterdump():
            out.write(f"{statement}\n")


def _add_uploads_tree(zf: zipfile.ZipFile, upload_dir: str) -> None:
    if not os.path.isdir(upload_dir):
        return
    for root, _, files in os.walk(upload_dir):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, upload_dir)
            zf.write(full, UPLOADS_PREFIX + rel.replace(os.sep, "/"))


def _alembic_revision(db: Session) -> str | None:
    try:
        row = db.execute(text("SELECT version_num FROM alembic_version")).first()
        return row[0] if row else None
    except Exception:
        return None


def _app_version() -> str:
    try:
        return version("testjam-api")
    except PackageNotFoundError:
        return "unknown"


def _safe_unlink(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def cleanup_archive(path: str) -> None:
    _safe_unlink(path)


def pg_dump_available() -> bool:
    return shutil.which("pg_dump") is not None


def _quote(cmd: list[str]) -> str:
    return " ".join(shlex.quote(c) for c in cmd)
