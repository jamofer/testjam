"""Project environments endpoints."""
from __future__ import annotations

from typing import Any

from testjam_client.errors import Conflict
from testjam_client.resources._base import Resource


class EnvironmentsResource(Resource):
    def list(self, project_id: int) -> list[dict]:
        return self._request("GET", f"/projects/{project_id}/environments").json()

    def create(self, project_id: int, slug: str, **payload: Any) -> dict:
        body = {"slug": slug, **payload}
        return self._request(
            "POST", f"/projects/{project_id}/environments", json=body,
        ).json()

    def find_or_create(self, project_id: int, slug: str, **payload: Any) -> dict:
        for environment in self.list(project_id):
            if environment.get("slug") == slug:
                return environment
        try:
            return self.create(project_id, slug, **payload)
        except Conflict:
            for environment in self.list(project_id):
                if environment.get("slug") == slug:
                    return environment
            raise
