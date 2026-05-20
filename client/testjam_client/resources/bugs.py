"""Bug tracking endpoints.

Covers the `/projects/{id}/bugs` and `/bugs/{id}` routers: CRUD, status
changes, comments, watchers, links, activity log, attachments, context
lookup, and the bug report exports.
"""
from __future__ import annotations

from typing import Any

from testjam_client.resources._base import Resource


class BugsResource(Resource):
    def list(
        self,
        project_id: int,
        *,
        status: str | None = None,
        severity: str | None = None,
        version_id: int | None = None,
        fixed_in_version_id: int | None = None,
        assigned_to_id: int | None = None,
        tag: str | None = None,
        search: str | None = None,
        cf_key: str | None = None,
        cf_value: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        if version_id is not None:
            params["version_id"] = version_id
        if fixed_in_version_id is not None:
            params["fixed_in_version_id"] = fixed_in_version_id
        if assigned_to_id is not None:
            params["assigned_to_id"] = assigned_to_id
        if tag is not None:
            params["tag"] = tag
        if search is not None:
            params["search"] = search
        if cf_key is not None:
            params["cf_key"] = cf_key
        if cf_value is not None:
            params["cf_value"] = cf_value
        return self._request(
            "GET", f"/projects/{project_id}/bugs", params=params,
        ).json()

    def get(self, bug_id: int) -> dict:
        return self._request("GET", f"/bugs/{bug_id}").json()

    def get_by_number(self, project_id: int, number: int) -> dict:
        return self._request(
            "GET", f"/projects/{project_id}/bugs/by-number/{number}",
        ).json()

    def create(
        self,
        project_id: int,
        title: str,
        *,
        description: str | None = None,
        severity: str = "medium",
        tags: list[str] | None = None,
        result_id: int | None = None,
        execution_id: int | None = None,
        version_id: int | None = None,
        fixed_in_version_id: int | None = None,
        environment: str | None = None,
        assigned_to_id: int | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> dict:
        body: dict[str, Any] = {"title": title, "severity": severity}
        if description is not None:
            body["description"] = description
        if tags is not None:
            body["tags"] = tags
        if result_id is not None:
            body["result_id"] = result_id
        if execution_id is not None:
            body["execution_id"] = execution_id
        if version_id is not None:
            body["version_id"] = version_id
        if fixed_in_version_id is not None:
            body["fixed_in_version_id"] = fixed_in_version_id
        if environment is not None:
            body["environment"] = environment
        if assigned_to_id is not None:
            body["assigned_to_id"] = assigned_to_id
        if custom_fields is not None:
            body["custom_fields"] = custom_fields
        return self._request(
            "POST", f"/projects/{project_id}/bugs", json=body,
        ).json()

    def update(self, bug_id: int, **payload: Any) -> dict:
        return self._request("PUT", f"/bugs/{bug_id}", json=payload).json()

    def delete(self, bug_id: int) -> None:
        self._request("DELETE", f"/bugs/{bug_id}")

    def change_status(
        self, bug_id: int, status: str, *, note: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"status": status}
        if note is not None:
            body["note"] = note
        return self._request(
            "POST", f"/bugs/{bug_id}/status", json=body,
        ).json()

    def context(self, bug_id: int) -> dict:
        return self._request("GET", f"/bugs/{bug_id}/context").json()

    def list_comments(self, bug_id: int) -> list[dict]:
        return self._request("GET", f"/bugs/{bug_id}/comments").json()

    def add_comment(self, bug_id: int, body: str) -> dict:
        return self._request(
            "POST", f"/bugs/{bug_id}/comments", json={"body": body},
        ).json()

    def update_comment(self, bug_id: int, comment_id: int, body: str) -> dict:
        return self._request(
            "PUT", f"/bugs/{bug_id}/comments/{comment_id}", json={"body": body},
        ).json()

    def delete_comment(self, bug_id: int, comment_id: int) -> None:
        self._request("DELETE", f"/bugs/{bug_id}/comments/{comment_id}")

    def list_watchers(self, bug_id: int) -> list[dict]:
        return self._request("GET", f"/bugs/{bug_id}/watchers").json()

    def watch(self, bug_id: int) -> dict:
        return self._request("POST", f"/bugs/{bug_id}/watch").json()

    def unwatch(self, bug_id: int) -> dict:
        return self._request("DELETE", f"/bugs/{bug_id}/watch").json()

    def list_links(self, bug_id: int) -> list[dict]:
        return self._request("GET", f"/bugs/{bug_id}/links").json()

    def add_link(
        self,
        bug_id: int,
        *,
        kind: str | None = None,
        label: str | None = None,
        url: str | None = None,
        execution_id: int | None = None,
        test_case_id: int | None = None,
        test_step_id: int | None = None,
        target_bug_id: int | None = None,
    ) -> dict:
        body: dict[str, Any] = {}
        if kind is not None:
            body["kind"] = kind
        if label is not None:
            body["label"] = label
        if url is not None:
            body["url"] = url
        if execution_id is not None:
            body["execution_id"] = execution_id
        if test_case_id is not None:
            body["test_case_id"] = test_case_id
        if test_step_id is not None:
            body["test_step_id"] = test_step_id
        if target_bug_id is not None:
            body["target_bug_id"] = target_bug_id
        return self._request(
            "POST", f"/bugs/{bug_id}/links", json=body,
        ).json()

    def delete_link(self, bug_id: int, link_id: int) -> None:
        self._request("DELETE", f"/bugs/{bug_id}/links/{link_id}")

    def list_activity(self, bug_id: int) -> list[dict]:
        return self._request("GET", f"/bugs/{bug_id}/activity").json()

    def list_attachments(self, bug_id: int) -> list[dict]:
        return self._request("GET", f"/bugs/{bug_id}/attachments").json()

    def download_report(
        self,
        project_id: int,
        *,
        format: str = "html",
        version_id: int | None = None,
        environment: str | None = None,
    ) -> bytes:
        params: dict[str, Any] = {"format": format}
        if version_id is not None:
            params["version_id"] = version_id
        if environment is not None:
            params["environment"] = environment
        response = self._request(
            "GET", f"/projects/{project_id}/bugs/report", params=params,
        )
        return response.content

    def download_release_notes(self, project_id: int) -> bytes:
        response = self._request(
            "GET", f"/projects/{project_id}/bugs/release-notes",
        )
        return response.content
