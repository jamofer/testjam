"""Mention resolver + autocomplete endpoints.

`resolve` enriches a list of parsed tokens (kind/slug/id/sub_ids) with display
labels, URLs, and accessibility flags — useful when a CLI or script wants to
pre-render markdown that contains mentions before posting it.

`search` powers autocomplete by ``kind`` (``user`` / ``bug`` / ``execution`` /
``case`` / ``result`` / ``step_result``). Returns up to ``limit`` hits.
"""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class MentionsResource(Resource):
    def resolve(self, project_id: int, tokens: list[dict]) -> list[dict]:
        body = {"tokens": tokens}
        response = self._request(
            "POST", f"/projects/{project_id}/mentions/resolve", json=body,
        )
        return response.json()["mentions"]

    def search(
        self,
        project_id: int,
        kind: str,
        *,
        q: str = "",
        limit: int = 10,
        execution_id: int | None = None,
        result_id: int | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {"kind": kind, "q": q, "limit": limit}
        if execution_id is not None:
            params["execution_id"] = execution_id
        if result_id is not None:
            params["result_id"] = result_id
        response = self._request(
            "GET", f"/projects/{project_id}/mentions/search", params=params,
        )
        return response.json()["hits"]
