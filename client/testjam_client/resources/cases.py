"""Test cases endpoints (incl. step replacement, archive, reconcile)."""
from __future__ import annotations

from typing import Any

from testjam_client.errors import Conflict
from testjam_client.resources._base import Resource


def _steps_differ(current: list[dict], spec: list[dict]) -> bool:
    if len(current) != len(spec):
        return True
    keys = ("action", "expected_result", "step_type")
    for c, s in zip(current, spec):
        for key in keys:
            default = "action" if key == "step_type" else None
            if c.get(key) != s.get(key, default):
                return True
    return False


class CasesResource(Resource):
    def list(
        self,
        suite_id: int,
        *,
        name: str | None = None,
        external_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict]:
        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if external_id is not None:
            params["external_id"] = external_id
        if include_archived:
            params["include_archived"] = True
        return self._request("GET", f"/suites/{suite_id}/cases", params=params).json()

    def get(self, case_id: int) -> dict:
        return self._request("GET", f"/cases/{case_id}").json()

    def create(
        self,
        suite_id: int,
        name: str,
        *,
        description: str | None = None,
        tags: list[str] | None = None,
        external_id: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"name": name, "suite_id": suite_id}
        if description is not None:
            body["description"] = description
        if tags is not None:
            body["tags"] = tags
        if external_id is not None:
            body["external_id"] = external_id
        return self._request("POST", f"/suites/{suite_id}/cases", json=body).json()

    def update(self, case_id: int, **payload: Any) -> dict:
        return self._request("PUT", f"/cases/{case_id}", json=payload).json()

    def delete(self, case_id: int) -> None:
        self._request("DELETE", f"/cases/{case_id}")

    def archive(self, case_id: int) -> dict:
        return self._request("POST", f"/cases/{case_id}/archive").json()

    def unarchive(self, case_id: int) -> dict:
        return self._request("POST", f"/cases/{case_id}/unarchive").json()

    def list_steps(self, case_id: int) -> list[dict]:
        return self._request("GET", f"/cases/{case_id}/steps").json()

    def add_step(
        self,
        case_id: int,
        action: str,
        *,
        expected_result: str | None = None,
        order: int | None = None,
        step_type: str = "action",
    ) -> dict:
        body: dict[str, Any] = {"action": action, "step_type": step_type}
        if expected_result is not None:
            body["expected_result"] = expected_result
        if order is not None:
            body["order"] = order
        return self._request("POST", f"/cases/{case_id}/steps", json=body).json()

    def update_step(self, case_id: int, step_id: int, **payload: Any) -> dict:
        return self._request(
            "PUT", f"/cases/{case_id}/steps/{step_id}", json=payload,
        ).json()

    def delete_step(self, case_id: int, step_id: int) -> None:
        self._request("DELETE", f"/cases/{case_id}/steps/{step_id}")

    def delete_steps_by_type(self, case_id: int, step_type: str) -> None:
        self._request(
            "DELETE", f"/cases/{case_id}/steps", params={"step_type": step_type},
        )

    def reorder_steps(self, case_id: int, step_ids: list[int]) -> list[dict]:
        return self._request(
            "POST", f"/cases/{case_id}/steps/reorder", json={"step_ids": step_ids},
        ).json()

    def replace_steps(self, case_id: int, steps: list[dict]) -> list[dict]:
        return self._request(
            "POST", f"/cases/{case_id}/steps/replace", json={"steps": steps},
        ).json()

    def reconcile(
        self,
        suite_id: int,
        specs: list[dict],
    ) -> dict[str, list[int]]:
        """Sync the suite's cases to match ``specs``.

        Each spec dict accepts: ``external_id`` (required, identity key),
        ``name`` (required), ``description``, ``tags``, ``steps`` (list of
        step dicts). Cases present in Testjam but absent in ``specs`` (matched
        by ``external_id``) are archived.

        Returns ``{"created": [...], "updated": [...], "archived": [...]}``.
        """
        existing = {
            c["external_id"]: c
            for c in self.list(suite_id, include_archived=False)
            if c.get("external_id")
        }
        seen_external_ids: set[str] = set()
        diff: dict[str, list[int]] = {"created": [], "updated": [], "archived": []}

        for spec in specs:
            external_id = spec.get("external_id")
            if not external_id:
                raise ValueError("Each spec requires an `external_id`")
            seen_external_ids.add(external_id)
            current = existing.get(external_id)
            steps = spec.get("steps")
            payload_attrs = {k: spec[k] for k in ("description", "tags") if k in spec}

            if current is None:
                created = self.create(
                    suite_id, spec["name"],
                    external_id=external_id, **payload_attrs,
                )
                if steps is not None:
                    self.replace_steps(created["id"], steps)
                diff["created"].append(created["id"])
                continue

            needs_update = current["name"] != spec["name"] or any(
                current.get(field) != value for field, value in payload_attrs.items()
            )
            if needs_update:
                self.update(current["id"], name=spec["name"], **payload_attrs)
            if steps is not None and _steps_differ(current.get("steps", []), steps):
                self.replace_steps(current["id"], steps)
                needs_update = True
            if needs_update:
                diff["updated"].append(current["id"])

        for external_id, case in existing.items():
            if external_id in seen_external_ids:
                continue
            self.archive(case["id"])
            diff["archived"].append(case["id"])

        return diff

    def parent_chain(self, case_id: int) -> list[dict]:
        """Suites from root → direct parent of ``case_id``."""
        case = self.get(case_id)
        suite = self._client.suites.get(case["suite_id"])
        return self._client.suites.parent_chain(suite["project_id"], suite["id"])

    def path(self, case_id: int, *, separator: str = ".") -> str:
        """Dotted full path including the case name, e.g.
        ``suiteA.suiteB.suiteC.case_name``."""
        case = self.get(case_id)
        suite = self._client.suites.get(case["suite_id"])
        prefix = self._client.suites.path(
            suite["project_id"], suite["id"], separator=separator,
        )
        return f"{prefix}{separator}{case['name']}" if prefix else case["name"]

    def find_or_create(
        self,
        suite_id: int,
        name: str,
        **kwargs: Any,
    ) -> dict:
        existing = [c for c in self.list(suite_id, name=name) if c["name"] == name]
        if existing:
            return existing[0]
        try:
            return self.create(suite_id, name, **kwargs)
        except Conflict:
            existing = [c for c in self.list(suite_id, name=name) if c["name"] == name]
            if not existing:
                raise
            return existing[0]
