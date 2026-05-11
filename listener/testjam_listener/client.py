"""HTTP client for the Testjam REST API."""
from __future__ import annotations

from typing import Any

import requests


class TestjamClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        if api_key:
            self.session.headers["X-API-Key"] = api_key

    def login_with_password(self, username: str, password: str) -> str:
        response = self.session.post(
            self._url("/auth/login"),
            data={"username": username, "password": password},
            timeout=self.timeout,
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        self.session.headers["Authorization"] = f"Bearer {token}"
        return token

    def list_projects(self) -> list[dict]:
        response = self.session.get(self._url("/projects"), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def create_project(self, name: str) -> dict:
        response = self.session.post(
            self._url("/projects"), json={"name": name}, timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def find_or_create_project(self, name: str) -> int:
        for project in self.list_projects():
            if project["name"] == name:
                return project["id"]
        return self.create_project(name)["id"]

    def find_or_create_suite(
        self,
        project_id: int,
        name: str,
        *,
        parent_suite_id: int | None = None,
        description: str | None = None,
    ) -> int | None:
        params: dict[str, Any] = {"name": name}
        if parent_suite_id is not None:
            params["parent_suite_id"] = parent_suite_id
        existing = self.session.get(
            self._url(f"/projects/{project_id}/suites"),
            params=params, timeout=self.timeout,
        )
        if existing.ok and existing.json():
            suite_id = existing.json()[0]["id"]
            if description:
                self.session.put(
                    self._url(f"/suites/{suite_id}"),
                    json={"description": description}, timeout=self.timeout,
                )
            return suite_id

        body: dict[str, Any] = {"name": name}
        if parent_suite_id is not None:
            body["parent_suite_id"] = parent_suite_id
        if description:
            body["description"] = description
        created = self.session.post(
            self._url(f"/projects/{project_id}/suites"),
            json=body, timeout=self.timeout,
        )
        return created.json()["id"] if created.ok else None

    def find_or_create_case(
        self,
        suite_id: int,
        name: str,
        *,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> int | None:
        existing = self.session.get(
            self._url(f"/suites/{suite_id}/cases"),
            params={"name": name}, timeout=self.timeout,
        )
        if existing.ok and existing.json():
            case_id = existing.json()[0]["id"]
            patch: dict[str, Any] = {"tags": tags or []}
            if description:
                patch["description"] = description
            self.session.put(
                self._url(f"/cases/{case_id}"), json=patch, timeout=self.timeout,
            )
            return case_id

        body: dict[str, Any] = {"name": name, "suite_id": suite_id, "tags": tags or []}
        if description:
            body["description"] = description
        created = self.session.post(
            self._url(f"/suites/{suite_id}/cases"),
            json=body, timeout=self.timeout,
        )
        return created.json()["id"] if created.ok else None

    def delete_all_case_steps(self, case_id: int) -> None:
        self.session.delete(self._url(f"/cases/{case_id}/steps"), timeout=self.timeout)

    def create_step(
        self,
        case_id: int,
        *,
        action: str,
        order: int,
        step_type: str = "action",
    ) -> int | None:
        response = self.session.post(
            self._url(f"/cases/{case_id}/steps"),
            json={"action": action, "step_type": step_type, "order": order},
            timeout=self.timeout,
        )
        return response.json()["id"] if response.ok else None

    def create_execution(
        self,
        project_id: int,
        *,
        title: str,
        type: str = "automatic",
    ) -> int:
        response = self.session.post(
            self._url(f"/projects/{project_id}/executions"),
            json={"title": title, "type": type}, timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["id"]

    def update_execution(self, execution_id: int, **payload: Any) -> None:
        self.session.put(
            self._url(f"/executions/{execution_id}"),
            json=payload, timeout=self.timeout,
        )

    def create_result(self, execution_id: int, **payload: Any) -> dict | None:
        response = self.session.post(
            self._url(f"/executions/{execution_id}/results"),
            json=payload, timeout=self.timeout,
        )
        return response.json() if response.ok else None

    def update_result(self, result_id: int, **payload: Any) -> requests.Response:
        return self.session.put(
            self._url(f"/results/{result_id}"),
            json=payload, timeout=self.timeout,
        )

    def start_step_result(self, result_id: int, step_id: int) -> dict:
        response = self.session.post(
            self._url(f"/results/{result_id}/step-results"),
            json={"step_id": step_id}, timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def update_step_result(
        self, result_id: int, step_result_id: int, **payload: Any,
    ) -> requests.Response:
        return self.session.put(
            self._url(f"/results/{result_id}/step-results/{step_result_id}"),
            json=payload, timeout=self.timeout,
        )

    def append_step_result_log(
        self,
        result_id: int,
        step_result_id: int,
        *,
        level: str,
        message: str,
        timestamp_iso: str | None = None,
    ) -> requests.Response:
        body: dict[str, Any] = {"level": level, "message": message}
        if timestamp_iso:
            body["ts"] = timestamp_iso
        return self.session.post(
            self._url(f"/results/{result_id}/step-results/{step_result_id}/log"),
            json=body, timeout=self.timeout,
        )

    def upload_execution_attachment(
        self,
        execution_id: int,
        *,
        filename: str,
        file_handle: Any,
        mime: str,
    ) -> None:
        self.session.post(
            self._url(f"/executions/{execution_id}/attachments"),
            files={"file": (filename, file_handle, mime)},
            timeout=self.timeout,
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"
