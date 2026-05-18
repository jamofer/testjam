"""Project versions endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.errors import Conflict
from testjam_client.resources._base import Resource


class VersionsResource(Resource):
    def list(self, project_id: int) -> list[dict]:
        return self._request("GET", f"/projects/{project_id}/versions").json()

    def get(self, version_id: int) -> dict:
        return self._request("GET", f"/versions/{version_id}").json()

    def create(
        self,
        project_id: int,
        name: str,
        *,
        tag: str | None = None,
        description: str | None = None,
        release_date: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"name": name}
        if tag is not None:
            body["tag"] = tag
        if description is not None:
            body["description"] = description
        if release_date is not None:
            body["release_date"] = release_date
        return self._request("POST", f"/projects/{project_id}/versions", json=body).json()

    def update(self, version_id: int, **payload: Any) -> dict:
        return self._request("PUT", f"/versions/{version_id}", json=payload).json()

    def delete(self, version_id: int) -> None:
        self._request("DELETE", f"/versions/{version_id}")

    def find_by_name(self, project_id: int, name: str) -> dict | None:
        for version in self.list(project_id):
            if version["name"] == name:
                return version
        return None

    def find_or_create(
        self,
        project_id: int,
        name: str,
        **kwargs: Any,
    ) -> dict:
        existing = self.find_by_name(project_id, name)
        if existing is not None:
            return existing
        try:
            return self.create(project_id, name, **kwargs)
        except Conflict:
            existing = self.find_by_name(project_id, name)
            if existing is None:
                raise
            return existing

    def list_attachments(self, version_id: int) -> list[dict]:
        return self._request("GET", f"/versions/{version_id}/attachments").json()

    def upload_attachment(
        self,
        version_id: int,
        *,
        filename: str,
        content,
        mime: str,
    ) -> dict:
        files = {"file": (filename, content, mime)}
        return self._request(
            "POST", f"/versions/{version_id}/attachments", files=files,
        ).json()

    def download_attachment(self, version_id: int, attachment_id: int) -> bytes:
        response = self._request(
            "GET", f"/versions/{version_id}/attachments/{attachment_id}/download",
        )
        return response.content

    def delete_attachment(self, version_id: int, attachment_id: int) -> None:
        self._request(
            "DELETE", f"/versions/{version_id}/attachments/{attachment_id}",
        )
