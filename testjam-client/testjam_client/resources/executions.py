"""Executions endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.models import Attachment, BulkResultResponse, Execution, Result
from testjam_client.resources._base import Resource

RERUN_ALL = "all"
RERUN_NOT_PASSED = "not_passed"


class ExecutionsResource(Resource):
    def list(
        self,
        project_id: int,
        *,
        type: str | None = None,
        status: str | None = None,
        assigned_to_id: int | None = None,
        version_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Execution]:
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if type is not None:
            params["type"] = type
        if status is not None:
            params["status"] = status
        if assigned_to_id is not None:
            params["assigned_to_id"] = assigned_to_id
        if version_id is not None:
            params["version_id"] = version_id
        return self._request(
            "GET", f"/projects/{project_id}/executions", params=params,
        ).json()

    def get(self, execution_id: int) -> Execution:
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
        custom_fields: dict[str, Any] | None = None,
    ) -> Execution:
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
        if custom_fields is not None:
            body["custom_fields"] = custom_fields
        return self._request(
            "POST", f"/projects/{project_id}/executions", json=body,
        ).json()

    def update(self, execution_id: int, **payload: Any) -> Execution:
        return self._request("PUT", f"/executions/{execution_id}", json=payload).json()

    def delete(self, execution_id: int) -> None:
        self._request("DELETE", f"/executions/{execution_id}")

    def reopen(self, execution_id: int) -> Execution:
        """Move a completed or aborted execution back to in progress."""
        return self._request("POST", f"/executions/{execution_id}/reopen").json()

    def rerun(self, execution_id: int, *, cases: str = RERUN_ALL) -> Execution:
        """Start a new execution from a finished one: every case (``all``) or only ``not_passed``."""
        return self._request(
            "POST", f"/executions/{execution_id}/rerun", json={"cases": cases},
        ).json()

    def list_results(self, execution_id: int, *, assigned_to_id: int | None = None) -> list[Result]:
        params = {"assigned_to_id": assigned_to_id} if assigned_to_id is not None else None
        return self._request("GET", f"/executions/{execution_id}/results", params=params).json()

    def bulk_results(self, execution_id: int, results: list[dict]) -> BulkResultResponse:
        """Create or update many results in one call; returns created/updated/errors counts."""
        return self._request(
            "POST", f"/executions/{execution_id}/results/bulk", json={"results": results},
        ).json()

    def import_junit(self, execution_id: int, *, filename: str, content) -> BulkResultResponse:
        """Apply a JUnit XML report to the execution's results."""
        return self._import(execution_id, "junit", filename, content)

    def import_robotframework(self, execution_id: int, *, filename: str, content) -> BulkResultResponse:
        """Apply a Robot Framework ``output.xml`` to the execution's results."""
        return self._import(execution_id, "robotframework", filename, content)

    def export_xlsx(self, execution_id: int) -> bytes:
        return self._request("GET", f"/executions/{execution_id}/export/xlsx").content

    def export_html(self, execution_id: int) -> str:
        return self._request("GET", f"/executions/{execution_id}/export/html").text

    def list_attachments(self, execution_id: int) -> list[Attachment]:
        return self._request("GET", f"/executions/{execution_id}/attachments").json()

    def upload_attachment(
        self,
        execution_id: int,
        *,
        filename: str,
        content,
        mime: str,
    ) -> Attachment:
        """Upload a file (log.html, output.xml, screenshot…) to the execution."""
        files = {"file": (filename, content, mime)}
        return self._request(
            "POST", f"/executions/{execution_id}/attachments", files=files,
        ).json()

    def _import(self, execution_id: int, kind: str, filename: str, content) -> BulkResultResponse:
        files = {"file": (filename, content, "application/xml")}
        return self._request(
            "POST", f"/executions/{execution_id}/results/import/{kind}", files=files,
        ).json()
