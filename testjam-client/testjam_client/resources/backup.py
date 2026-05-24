"""Admin-only backup download.

The API ships the whole instance as a single zip (manifest + SQL dump +
uploads tree) over ``GET /settings/backup``. This resource exposes both
a "give me the bytes" path for callers that want to handle persistence
themselves and a "save to disk" path that takes care of streaming and
filename resolution.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from testjam_client.resources._base import Resource


class BackupResource(Resource):
    def download_bytes(self) -> bytes:
        response = self._request("GET", "/settings/backup")
        return response.content

    def download(self, destination: str | os.PathLike[str]) -> Path:
        """Save the backup archive to ``destination``.

        If ``destination`` is an existing directory (or a path that ends in
        a separator), the filename is taken from the API's
        ``Content-Disposition`` header when present, otherwise it falls
        back to ``testjam-backup.zip``. Returns the full path written.
        """
        response = self._request("GET", "/settings/backup")
        target = Path(destination)
        if target.is_dir() or str(destination).endswith(os.sep):
            target.mkdir(parents=True, exist_ok=True)
            filename = _filename_from_response(response, fallback="testjam-backup.zip")
            target = target / filename
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        return target


def _filename_from_response(response, *, fallback: str) -> str:
    disposition = ""
    headers = getattr(response, "headers", None)
    if headers is not None:
        disposition = headers.get("content-disposition", "") or ""
    match = re.search(r'filename="?([^";]+)"?', disposition)
    if not match:
        return fallback
    return match.group(1).strip() or fallback
