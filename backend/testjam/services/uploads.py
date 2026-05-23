"""Shared helpers for attachment and import uploads.

Sanitizes user-supplied filenames to prevent path traversal and enforces
an upper bound on the byte count read from incoming UploadFile streams.
"""
from __future__ import annotations

import os
from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile

FALLBACK_FILENAME = "attachment"
DEFAULT_CHUNK = 64 * 1024


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


def read_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """Read the upload fully into memory, refusing when it exceeds ``max_bytes``.

    Streams in chunks so an oversized request is rejected without slurping the
    full payload into RAM first.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = file.file.read(DEFAULT_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds {max_bytes} byte limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)
