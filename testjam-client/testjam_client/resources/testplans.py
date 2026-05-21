"""Test plan endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class TestPlansResource(Resource):
    def list(self, project_id: int) -> list[dict]:
        return self._request("GET", f"/projects/{project_id}/plans").json()

    def get(self, plan_id: int) -> dict:
        return self._request("GET", f"/plans/{plan_id}").json()

    def create(
        self,
        project_id: int,
        title: str,
        *,
        description: str | None = None,
        test_case_ids: list[int] | None = None,
    ) -> dict:
        body: dict[str, Any] = {"title": title}
        if description is not None:
            body["description"] = description
        if test_case_ids is not None:
            body["test_case_ids"] = test_case_ids
        return self._request(
            "POST", f"/projects/{project_id}/plans", json=body,
        ).json()

    def update(self, plan_id: int, **payload: Any) -> dict:
        return self._request("PUT", f"/plans/{plan_id}", json=payload).json()

    def delete(self, plan_id: int) -> None:
        self._request("DELETE", f"/plans/{plan_id}")

    def add_cases(self, plan_id: int, case_ids: list[int]) -> dict:
        return self._request(
            "POST", f"/plans/{plan_id}/cases", json={"case_ids": case_ids},
        ).json()
