"""Projects endpoints."""
from __future__ import annotations

from testjam_client.errors import Conflict
from testjam_client.resources._base import Resource


class ProjectsResource(Resource):
    def list(self) -> list[dict]:
        return self._request("GET", "/projects").json()

    def get(self, project_id: int) -> dict:
        return self._request("GET", f"/projects/{project_id}").json()

    def create(self, name: str, *, description: str | None = None) -> dict:
        body: dict = {"name": name}
        if description is not None:
            body["description"] = description
        return self._request("POST", "/projects", json=body).json()

    def delete(self, project_id: int) -> None:
        self._request("DELETE", f"/projects/{project_id}")

    def find_by_name(self, name: str) -> dict | None:
        for project in self.list():
            if project["name"] == name:
                return project
        return None

    def find_or_create(self, name: str, *, description: str | None = None) -> dict:
        existing = self.find_by_name(name)
        if existing is not None:
            return existing
        try:
            return self.create(name, description=description)
        except Conflict:
            existing = self.find_by_name(name)
            if existing is None:
                raise
            return existing
