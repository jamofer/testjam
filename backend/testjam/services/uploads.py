"""Shared helpers for attachment uploads.

Sanitizes user-supplied filenames to prevent path traversal: a malicious
client sending ``../../etc/secret`` as the file name would otherwise be
joined into ``os.path.join(upload_dir, file.filename)`` and escape the
intended destination.
"""
from __future__ import annotations

import os
from pathlib import PurePosixPath

FALLBACK_FILENAME = "attachment"


def safe_filename(raw: str | None) -> str:
    """Strip any directory components and forbid empty / dotfile-only names.

    Always returns a plain file name (no separators). Falls back to a
    constant when the input collapses to nothing.
    """
    if not raw:
        return FALLBACK_FILENAME
    normalized = raw.replace("\\", "/").strip()
    candidate = PurePosixPath(normalized).name
    candidate = candidate.strip().strip("/\\")
    candidate = candidate.lstrip(".")
    return candidate or FALLBACK_FILENAME


def safe_join(directory: str, raw_filename: str | None) -> str:
    """Return ``directory/<sanitized filename>`` and assert containment."""
    name = safe_filename(raw_filename)
    destination = os.path.realpath(os.path.join(directory, name))
    root = os.path.realpath(directory)
    if not destination.startswith(root + os.sep) and destination != root:
        return os.path.join(root, FALLBACK_FILENAME)
    return destination
