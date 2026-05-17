"""Test result endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class ResultsResource(Resource):
    def get(self, result_id: int) -> dict:
        return self._request("GET", f"/results/{result_id}").json()

    def create(
        self,
        execution_id: int,
        *,
        test_case_id: int,
        status: str = "not_run",
        comment: str | None = None,
        executed_by: str | None = None,
        duration_ms: int | None = None,
        step_results: list[dict] | None = None,
    ) -> dict:
        body: dict[str, Any] = {"test_case_id": test_case_id, "status": status}
        if comment is not None:
            body["comment"] = comment
        if executed_by is not None:
            body["executed_by"] = executed_by
        if duration_ms is not None:
            body["duration_ms"] = duration_ms
        if step_results is not None:
            body["step_results"] = step_results
        return self._request(
            "POST", f"/executions/{execution_id}/results", json=body,
        ).json()

    def update(self, result_id: int, **payload: Any) -> dict:
        return self._request("PUT", f"/results/{result_id}", json=payload).json()
