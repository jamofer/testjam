"""Test suites endpoints (hierarchical)."""
from __future__ import annotations

from typing import Any

from testjam_client.errors import Conflict
from testjam_client.resources._base import Resource


class SuitesResource(Resource):
    def list(
        self,
        project_id: int,
        *,
        parent_suite_id: int | None = None,
        all: bool = False,
    ) -> list[dict]:
        params: dict[str, Any] = {}
        if parent_suite_id is not None:
            params["parent_suite_id"] = parent_suite_id
        if all:
            params["all"] = True
        return self._request(
            "GET", f"/projects/{project_id}/suites", params=params,
        ).json()

    def get(self, suite_id: int) -> dict:
        return self._request("GET", f"/suites/{suite_id}").json()

    def create(
        self,
        project_id: int,
        name: str,
        *,
        parent_suite_id: int | None = None,
        description: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"name": name}
        if parent_suite_id is not None:
            body["parent_suite_id"] = parent_suite_id
        if description is not None:
            body["description"] = description
        return self._request(
            "POST", f"/projects/{project_id}/suites", json=body,
        ).json()

    def update(self, suite_id: int, **payload: Any) -> dict:
        return self._request("PUT", f"/suites/{suite_id}", json=payload).json()

    def delete(self, suite_id: int) -> None:
        self._request("DELETE", f"/suites/{suite_id}")

    def descendants(self, project_id: int, suite_id: int) -> list[dict]:
        """Every sub-suite under ``suite_id`` (recursive, excludes itself)."""
        by_parent: dict[int | None, list[dict]] = {}
        for suite in self.list(project_id, all=True):
            by_parent.setdefault(suite.get("parent_suite_id"), []).append(suite)
        out: list[dict] = []
        stack = list(by_parent.get(suite_id, []))
        while stack:
            current = stack.pop()
            out.append(current)
            stack.extend(by_parent.get(current["id"], []))
        return out

    def case_ids_recursive(self, project_id: int, suite_id: int) -> list[int]:
        """All TestCase ids under ``suite_id`` + every sub-suite."""
        root = self.get(suite_id)
        ids = list(root.get("test_case_ids", []))
        for sub in self.descendants(project_id, suite_id):
            ids.extend(sub.get("test_case_ids", []))
        return ids

    def parent_chain(self, project_id: int, suite_id: int) -> list[dict]:
        """Suites from root → ... → ``suite_id`` inclusive."""
        all_suites = {s["id"]: s for s in self.list(project_id, all=True)}
        chain: list[dict] = []
        cursor: int | None = suite_id
        while cursor is not None:
            current = all_suites.get(cursor)
            if current is None:
                break
            chain.append(current)
            cursor = current.get("parent_suite_id")
        return list(reversed(chain))

    def path(self, project_id: int, suite_id: int, *, separator: str = ".") -> str:
        """Dotted full path of a suite, e.g. ``suiteA.suiteB.suiteC``."""
        return separator.join(s["name"] for s in self.parent_chain(project_id, suite_id))

    def find_or_create(
        self,
        project_id: int,
        name: str,
        *,
        parent_suite_id: int | None = None,
        description: str | None = None,
    ) -> dict:
        existing = [
            suite for suite in self.list(project_id, parent_suite_id=parent_suite_id)
            if suite["name"] == name
        ]
        if existing:
            return existing[0]
        try:
            return self.create(
                project_id, name,
                parent_suite_id=parent_suite_id, description=description,
            )
        except Conflict:
            existing = [
                suite for suite in self.list(project_id, parent_suite_id=parent_suite_id)
                if suite["name"] == name
            ]
            if not existing:
                raise
            return existing[0]
