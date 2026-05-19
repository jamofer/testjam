"""Outbound webhook endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class WebhooksResource(Resource):
    def list(self, project_id: int) -> list[dict]:
        return self._request("GET", f"/projects/{project_id}/webhooks").json()

    def get(self, webhook_id: int) -> dict:
        return self._request("GET", f"/webhooks/{webhook_id}").json()

    def create(
        self,
        project_id: int,
        *,
        name: str,
        url: str,
        events: list[str],
        is_active: bool = True,
    ) -> dict:
        body: dict[str, Any] = {
            "name": name,
            "url": url,
            "events": events,
            "is_active": is_active,
        }
        return self._request(
            "POST", f"/projects/{project_id}/webhooks", json=body,
        ).json()

    def update(self, webhook_id: int, **payload: Any) -> dict:
        return self._request(
            "PUT", f"/webhooks/{webhook_id}", json=payload,
        ).json()

    def delete(self, webhook_id: int) -> None:
        self._request("DELETE", f"/webhooks/{webhook_id}")

    def test(self, webhook_id: int) -> dict:
        return self._request("POST", f"/webhooks/{webhook_id}/test").json()

    def list_deliveries(self, webhook_id: int, *, limit: int = 25) -> list[dict]:
        return self._request(
            "GET", f"/webhooks/{webhook_id}/deliveries",
            params={"limit": limit},
        ).json()
