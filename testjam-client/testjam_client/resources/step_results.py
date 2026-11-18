"""Step result endpoints (start/update/log)."""
from __future__ import annotations

from typing import Any

from testjam_client.models import StepResult
from testjam_client.resources._base import Resource


class StepResultsResource(Resource):
    def start(
        self, result_id: int, step_id: int, *, arguments: list[str] | None = None,
    ) -> StepResult:
        body: dict[str, Any] = {"step_id": step_id}
        if arguments is not None:
            body["arguments"] = arguments
        return self._request(
            "POST", f"/results/{result_id}/step-results", json=body,
        ).json()

    def update(self, result_id: int, step_result_id: int, **payload: Any) -> StepResult:
        return self._request(
            "PUT", f"/results/{result_id}/step-results/{step_result_id}",
            json=payload,
        ).json()

    def append_log(
        self,
        result_id: int,
        step_result_id: int,
        *,
        level: str,
        message: str,
        ts: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"level": level, "message": message}
        if ts is not None:
            body["ts"] = ts
        return self._request(
            "POST", f"/results/{result_id}/step-results/{step_result_id}/log",
            json=body,
        ).json()
