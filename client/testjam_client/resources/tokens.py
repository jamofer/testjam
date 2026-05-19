"""User and project API token endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class TokensResource(Resource):
    # ---- user tokens (/users/me/tokens) ----

    def list_user_tokens(self) -> list[dict]:
        return self._request("GET", "/users/me/tokens").json()

    def create_user_token(
        self, name: str, *, expires_at: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expires_at"] = expires_at
        return self._request("POST", "/users/me/tokens", json=body).json()

    def rotate_user_token(self, token_id: int) -> dict:
        return self._request(
            "POST", f"/users/me/tokens/{token_id}/rotate",
        ).json()

    def delete_user_token(self, token_id: int) -> None:
        self._request("DELETE", f"/users/me/tokens/{token_id}")

    # ---- project tokens (/projects/{id}/tokens) ----

    def list_project_tokens(self, project_id: int) -> list[dict]:
        return self._request(
            "GET", f"/projects/{project_id}/tokens",
        ).json()

    def create_project_token(
        self, project_id: int, name: str, *, expires_at: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expires_at"] = expires_at
        return self._request(
            "POST", f"/projects/{project_id}/tokens", json=body,
        ).json()

    def rotate_project_token(self, project_id: int, token_id: int) -> dict:
        return self._request(
            "POST", f"/projects/{project_id}/tokens/{token_id}/rotate",
        ).json()

    def delete_project_token(self, project_id: int, token_id: int) -> None:
        self._request(
            "DELETE", f"/projects/{project_id}/tokens/{token_id}",
        )
