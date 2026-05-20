"""Custom field definition endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class CustomFieldsResource(Resource):
    def list(
        self,
        project_id: int,
        entity_type: str,
        *,
        include_archived: bool = False,
    ) -> list[dict]:
        params: dict[str, Any] = {"entity_type": entity_type}
        if include_archived:
            params["include_archived"] = True
        return self._request(
            "GET", f"/projects/{project_id}/custom-fields", params=params,
        ).json()

    def get(self, field_id: int) -> dict:
        return self._request("GET", f"/custom-fields/{field_id}").json()

    def create(
        self,
        project_id: int,
        *,
        entity_type: str,
        key: str,
        label: str,
        type: str,
        options: list[dict] | None = None,
        required: bool = False,
        default_value: Any = None,
    ) -> dict:
        body: dict[str, Any] = {
            "entity_type": entity_type,
            "key": key,
            "label": label,
            "type": type,
            "required": required,
        }
        if options is not None:
            body["options"] = options
        if default_value is not None:
            body["default_value"] = default_value
        return self._request(
            "POST", f"/projects/{project_id}/custom-fields", json=body,
        ).json()

    def update(self, field_id: int, **payload: Any) -> dict:
        return self._request(
            "PUT", f"/custom-fields/{field_id}", json=payload,
        ).json()

    def delete(self, field_id: int) -> None:
        self._request("DELETE", f"/custom-fields/{field_id}")

    def archive(self, field_id: int) -> dict:
        return self._request("POST", f"/custom-fields/{field_id}/archive").json()

    def unarchive(self, field_id: int) -> dict:
        return self._request("POST", f"/custom-fields/{field_id}/unarchive").json()

    def reorder(self, project_id: int, ids: list[int]) -> list[dict]:
        return self._request(
            "POST",
            f"/projects/{project_id}/custom-fields/reorder",
            json={"ids": ids},
        ).json()
