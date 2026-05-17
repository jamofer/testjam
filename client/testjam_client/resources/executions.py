"""Executions endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class ExecutionsResource(Resource):
    def list(self, project_id: int) -> list[dict]:
        return self._request("GET", f"/projects/{project_id}/executions").json()

    def get(self, execution_id: int) -> dict:
        return self._request("GET", f"/executions/{execution_id}").json()

    def create(
        self,
        project_id: int,
        *,
        title: str,
        type: str = "manual",
        test_case_ids: list[int] | None = None,
        version_id: int | None = None,
        environment: str | None = None,
        description: str | None = None,
        assigned_to_id: int | None = None,
        triggered_by: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"title": title, "type": type}
        if test_case_ids is not None:
            body["test_case_ids"] = test_case_ids
        if version_id is not None:
            body["version_id"] = version_id
        if environment is not None:
            body["environment"] = environment
        if description is not None:
            body["description"] = description
        if assigned_to_id is not None:
            body["assigned_to_id"] = assigned_to_id
        if triggered_by is not None:
            body["triggered_by"] = triggered_by
        return self._request(
            "POST", f"/projects/{project_id}/executions", json=body,
        ).json()

    def update(self, execution_id: int, **payload: Any) -> dict:
        return self._request("PUT", f"/executions/{execution_id}", json=payload).json()

    def delete(self, execution_id: int) -> None:
        self._request("DELETE", f"/executions/{execution_id}")

    def list_results(self, execution_id: int) -> list[dict]:
        return self._request("GET", f"/executions/{execution_id}/results").json()

    def upload_attachment(
        self,
        execution_id: int,
        *,
        filename: str,
        content,
        mime: str,
    ) -> dict:
        """Upload a file (log.html, output.xml, screenshot…) to the execution."""
        files = {"file": (filename, content, mime)}
        return self._request(
            "POST", f"/executions/{execution_id}/attachments", files=files,
        ).json()
