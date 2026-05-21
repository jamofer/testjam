"""Public-share tokens for reports."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class PublicReportsResource(Resource):
    def list(self, project_id: int) -> list[dict]:
        return self._request("GET", f"/projects/{project_id}/public-reports").json()

    def create(
        self,
        project_id: int,
        *,
        kind: str,
        label: str | None = None,
        execution_id: int | None = None,
        version_id: int | None = None,
        environment: str | None = None,
        expires_at: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"kind": kind}
        if label is not None:
            payload["label"] = label
        if execution_id is not None:
            payload["execution_id"] = execution_id
        if version_id is not None:
            payload["version_id"] = version_id
        if environment is not None:
            payload["environment"] = environment
        if expires_at is not None:
            payload["expires_at"] = expires_at
        return self._request(
            "POST", f"/projects/{project_id}/public-reports", json=payload,
        ).json()

    def revoke(self, project_id: int, public_report_id: int) -> None:
        self._request(
            "DELETE",
            f"/projects/{project_id}/public-reports/{public_report_id}",
        )

    def fetch_html(self, token: str) -> str:
        return self._request("GET", f"/public/reports/{token}").text
