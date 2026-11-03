"""Remove attachment files from disk once their rows are deleted for good.

Rows can disappear directly or through an ORM cascade (deleting a project,
suite, case, execution, result, version or bug). Files are collected at
flush time and removed only after the transaction commits, so a rollback
never leaves a row pointing at a missing file.
"""
from __future__ import annotations

import contextlib
import os

from sqlalchemy import event
from sqlalchemy.orm import Session

from testjam.models.bug import BugAttachment
from testjam.models.execution import ExecutionAttachment, ResultAttachment
from testjam.models.testcase import Attachment
from testjam.models.version import VersionAttachment

ATTACHMENT_MODELS = (Attachment, BugAttachment, ExecutionAttachment, ResultAttachment, VersionAttachment)
PENDING_REMOVALS_KEY = "attachment_files_pending_removal"


def register() -> None:
    """Hook file cleanup into every ORM session. Safe to call more than once."""
    for event_name, listener in (
        ("after_flush", _collect_deleted_files),
        ("after_commit", _remove_collected_files),
        ("after_rollback", _forget_collected_files),
    ):
        if not event.contains(Session, event_name, listener):
            event.listen(Session, event_name, listener)


def _collect_deleted_files(session: Session, _flush_context) -> None:
    deleted_paths = [
        instance.file_path for instance in session.deleted if isinstance(instance, ATTACHMENT_MODELS)
    ]
    if deleted_paths:
        session.info.setdefault(PENDING_REMOVALS_KEY, []).extend(deleted_paths)


def _remove_collected_files(session: Session) -> None:
    for path in session.info.pop(PENDING_REMOVALS_KEY, []):
        with contextlib.suppress(FileNotFoundError):
            os.remove(path)


def _forget_collected_files(session: Session) -> None:
    session.info.pop(PENDING_REMOVALS_KEY, None)
