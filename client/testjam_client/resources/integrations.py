"""Integrations + bug external link endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class IntegrationsResource(Resource):
    def list_providers(self) -> list[dict]:
        return self._request("GET", "/integrations/providers").json()

    def list(self, project_id: int) -> list[dict]:
        return self._request("GET", f"/projects/{project_id}/integrations").json()

    def get(self, integration_id: int) -> dict:
        return self._request("GET", f"/integrations/{integration_id}").json()

    def create(
        self,
        project_id: int,
        *,
        provider: str,
        name: str,
        config: dict[str, Any],
        secret: str,
        status_mapping: dict[str, str] | None = None,
        is_active: bool = True,
    ) -> dict:
        payload: dict[str, Any] = {
            "provider": provider,
            "name": name,
            "config": config,
            "secret": secret,
            "is_active": is_active,
        }
        if status_mapping is not None:
            payload["status_mapping"] = status_mapping
        return self._request(
            "POST", f"/projects/{project_id}/integrations", json=payload,
        ).json()

    def update(self, integration_id: int, **payload: Any) -> dict:
        return self._request(
            "PUT", f"/integrations/{integration_id}", json=payload,
        ).json()

    def delete(self, integration_id: int) -> None:
        self._request("DELETE", f"/integrations/{integration_id}")

    def test(self, integration_id: int) -> None:
        self._request("POST", f"/integrations/{integration_id}/test")

    def rotate_credential(self, integration_id: int, *, secret: str) -> dict:
        return self._request(
            "POST", f"/integrations/{integration_id}/rotate-credential",
            json={"secret": secret},
        ).json()

    def list_bug_links(self, bug_id: int) -> list[dict]:
        return self._request("GET", f"/bugs/{bug_id}/external-links").json()

    def push_bug(
        self, bug_id: int, *, integration_id: int, labels: list[str] | None = None,
    ) -> dict:
        return self._request(
            "POST", f"/bugs/{bug_id}/external-links",
            json={"integration_id": integration_id, "labels": labels or []},
        ).json()

    def sync_bug_link(self, bug_id: int, link_id: int) -> dict:
        return self._request(
            "POST", f"/bugs/{bug_id}/external-links/{link_id}/sync",
        ).json()

    def delete_bug_link(self, bug_id: int, link_id: int) -> None:
        self._request("DELETE", f"/bugs/{bug_id}/external-links/{link_id}")

    def report_from_result(
        self,
        result_id: int,
        *,
        title: str,
        description: str | None = None,
        severity: str | None = None,
        tags: list[str] | None = None,
        integration_id: int | None = None,
        labels: list[str] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"title": title}
        if description is not None:
            payload["description"] = description
        if severity is not None:
            payload["severity"] = severity
        if tags is not None:
            payload["tags"] = tags
        if integration_id is not None:
            payload["integration_id"] = integration_id
        if labels is not None:
            payload["labels"] = labels
        return self._request(
            "POST", f"/results/{result_id}/report-external", json=payload,
        ).json()
