"""Azure DevOps (Boards) work-item provider.

Auth: PAT via HTTP Basic ``:<pat>`` (empty username), per the official docs.
Endpoint shape (REST 7.1):

- Create: ``POST {organization_url}/{project}/_apis/wit/workitems/${type}?api-version=7.1``
  body: ``application/json-patch+json`` JSON Patch ops.
- Status: ``GET {organization_url}/{project}/_apis/wit/workitems/{id}?api-version=7.1``
  reads ``fields["System.State"]``.

State names depend on the team's process template (Agile/Scrum/Basic). We
ship a default ``status_mapping`` that covers the common terminals
(``Closed``, ``Done``, ``Resolved``, ``Removed``) and treats anything else
as open. Users can override per-integration.
"""
from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import httpx

from testjam.core.config import settings
from testjam.services.integrations.base import (
    ExternalTicket,
    NormalizedStatus,
    ProviderConfigError,
    ProviderRequestError,
    register_provider,
)
from testjam.services.integrations.markdown_to_html import to_html


_DEFAULT_STATUS_MAPPING = {
    "Closed": "closed",
    "Done": "closed",
    "Resolved": "closed",
    "Removed": "closed",
    "New": "open",
    "Active": "open",
    "Committed": "open",
    "Approved": "open",
    "To Do": "open",
    "Doing": "open",
}
_CLOSED_TERMS = {"closed", "done", "resolved", "removed"}
_API_VERSION = "7.1"


class AzureDevOpsProvider:
    key = "azure_devops"
    label = "Azure DevOps Boards"

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        organization_url = (config.get("organization_url") or "").strip().rstrip("/")
        project = (config.get("project") or "").strip()
        work_item_type = (config.get("work_item_type") or "Bug").strip()
        if not organization_url:
            raise ProviderConfigError(
                "organization_url is required (e.g. https://dev.azure.com/acme)",
            )
        if not project:
            raise ProviderConfigError("project is required")
        return {
            "organization_url": organization_url,
            "project": project,
            "work_item_type": work_item_type,
        }

    def health_check(self, config: dict[str, Any], secret: str) -> None:
        if not secret:
            raise ProviderConfigError("API token is required")
        url = self._project_url(config) + "/_apis/wit/workitemtypes" + f"?api-version={_API_VERSION}"
        response = self._request("GET", url, secret)
        if response.status_code == 404:
            raise ProviderConfigError("Azure DevOps project not found or token lacks access")
        if response.status_code == 401 or response.status_code == 403:
            raise ProviderConfigError("Azure DevOps rejected the token")
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Azure DevOps health check failed ({response.status_code})",
                status_code=response.status_code,
            )

    def create_ticket(
        self,
        config: dict[str, Any],
        secret: str,
        *,
        title: str,
        body_markdown: str,
        labels: list[str] | None = None,
    ) -> ExternalTicket:
        work_item_type = quote(config["work_item_type"], safe="")
        url = (
            f"{self._project_url(config)}/_apis/wit/workitems/${work_item_type}"
            f"?api-version={_API_VERSION}"
        )
        patch: list[dict[str, Any]] = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": to_html(body_markdown or "")},
        ]
        if labels:
            patch.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": "; ".join(label.strip() for label in labels if label.strip()),
            })
        response = self._request(
            "POST", url, secret,
            json=patch,
            extra_headers={"Content-Type": "application/json-patch+json"},
        )
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Azure DevOps work-item creation failed ({response.status_code}): {response.text[:200]}",
                status_code=response.status_code,
            )
        item = response.json()
        external_id = str(item.get("id"))
        web_url = (item.get("_links", {}).get("html", {}) or {}).get("href")
        if not web_url:
            web_url = self._web_item_url(config, external_id)
        state = (item.get("fields", {}) or {}).get("System.State")
        return ExternalTicket(
            external_id=external_id,
            url=web_url,
            status_raw=state,
            status_normalized=self.normalize_status(state, {}),
            raw_payload=item,
        )

    def fetch_status(
        self, config: dict[str, Any], secret: str, external_id: str,
    ) -> ExternalTicket:
        url = (
            f"{self._project_url(config)}/_apis/wit/workitems/{external_id}"
            f"?api-version={_API_VERSION}"
        )
        response = self._request("GET", url, secret)
        if response.status_code == 404:
            return ExternalTicket(
                external_id=external_id,
                url=self._web_item_url(config, external_id),
                status_raw=None,
                status_normalized="unknown",
            )
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Azure DevOps status fetch failed ({response.status_code})",
                status_code=response.status_code,
            )
        item = response.json()
        state = (item.get("fields", {}) or {}).get("System.State")
        web_url = (item.get("_links", {}).get("html", {}) or {}).get("href")
        if not web_url:
            web_url = self._web_item_url(config, external_id)
        return ExternalTicket(
            external_id=external_id,
            url=web_url,
            status_raw=state,
            status_normalized=self.normalize_status(state, {}),
            raw_payload=item,
        )

    def normalize_status(
        self, status_raw: str | None, status_mapping: dict[str, str],
    ) -> NormalizedStatus:
        if status_raw is None:
            return "unknown"
        merged = {**_DEFAULT_STATUS_MAPPING, **status_mapping}
        if status_raw in merged:
            value = merged[status_raw]
            if value in ("open", "closed", "unknown"):
                return value  # type: ignore[return-value]
        if status_raw.lower() in _CLOSED_TERMS:
            return "closed"
        return "open"

    def _project_url(self, config: dict[str, Any]) -> str:
        project = quote(config["project"], safe="")
        return f"{config['organization_url']}/{project}"

    def _web_item_url(self, config: dict[str, Any], external_id: str) -> str:
        project = quote(config["project"], safe="")
        return f"{config['organization_url']}/{project}/_workitems/edit/{external_id}"

    def _request(
        self, method: str, url: str, secret: str,
        *,
        extra_headers: dict[str, str] | None = None,
        **kwargs,
    ):
        token = base64.b64encode(f":{secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        timeout = settings.INTEGRATION_HTTP_TIMEOUT_SECONDS
        try:
            with httpx.Client(timeout=timeout) as http:
                return http.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"Azure DevOps request failed: {exc}") from exc


register_provider(AzureDevOpsProvider())
