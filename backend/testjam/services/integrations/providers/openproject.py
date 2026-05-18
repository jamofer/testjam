"""OpenProject (API v3) work-package provider.

Auth: per-user API key sent as HTTP Basic with the literal username ``apikey``
and the token as the password — the documented form for OpenProject.

Endpoints:

- Create: ``POST {base}/api/v3/projects/{project}/work_packages`` body
  ``{subject, description: {raw}, _links: {type: {href: "/api/v3/types/N"}}}``.
- Status: ``GET {base}/api/v3/work_packages/{id}``. We read the status name
  from ``_embedded.status.name`` (preferred) or ``_links.status.title``.

OpenProject types are numeric ids per instance. We expose ``type_id`` on the
integration config so users can wire the type they want (Bug, Task, …)
without us hardcoding install-specific values.
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


_DEFAULT_STATUS_MAPPING = {
    "Closed": "closed",
    "Resolved": "closed",
    "Rejected": "closed",
    "Done": "closed",
    "On hold": "open",
    "In progress": "open",
    "New": "open",
}
_CLOSED_TERMS = {"closed", "resolved", "rejected", "done"}


class OpenProjectProvider:
    key = "openproject"
    label = "OpenProject"

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        base_url = (config.get("base_url") or "").strip().rstrip("/")
        project = (config.get("project") or "").strip()
        type_id_raw = config.get("type_id")
        if not base_url:
            raise ProviderConfigError("base_url is required (e.g. https://openproject.example.org)")
        if not project:
            raise ProviderConfigError("project is required (numeric id or identifier)")
        type_id: int | None
        if type_id_raw in (None, ""):
            type_id = None
        else:
            try:
                type_id = int(type_id_raw)
            except (TypeError, ValueError) as exc:
                raise ProviderConfigError("type_id must be a numeric work-package type id") from exc
        out: dict[str, Any] = {"base_url": base_url, "project": project}
        if type_id is not None:
            out["type_id"] = type_id
        return out

    def health_check(self, config: dict[str, Any], secret: str) -> None:
        if not secret:
            raise ProviderConfigError("API key is required")
        url = f"{config['base_url']}/api/v3/projects/{quote(config['project'], safe='')}"
        response = self._request("GET", url, secret)
        if response.status_code == 404:
            raise ProviderConfigError("OpenProject project not found or token lacks access")
        if response.status_code in (401, 403):
            raise ProviderConfigError("OpenProject rejected the API key")
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"OpenProject health check failed ({response.status_code})",
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
        project = quote(config["project"], safe="")
        url = f"{config['base_url']}/api/v3/projects/{project}/work_packages"
        payload: dict[str, Any] = {
            "subject": title,
            "description": {"raw": body_markdown or ""},
        }
        if "type_id" in config:
            payload["_links"] = {"type": {"href": f"/api/v3/types/{config['type_id']}"}}
        response = self._request("POST", url, secret, json=payload)
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"OpenProject work-package creation failed ({response.status_code}): {response.text[:200]}",
                status_code=response.status_code,
            )
        item = response.json()
        external_id = str(item.get("id"))
        status_name = _extract_status_name(item)
        web_url = _extract_web_url(config, item, external_id)
        return ExternalTicket(
            external_id=external_id,
            url=web_url,
            status_raw=status_name,
            status_normalized=self.normalize_status(status_name, {}),
            raw_payload=item,
        )

    def fetch_status(
        self, config: dict[str, Any], secret: str, external_id: str,
    ) -> ExternalTicket:
        url = f"{config['base_url']}/api/v3/work_packages/{external_id}"
        response = self._request("GET", url, secret)
        if response.status_code == 404:
            return ExternalTicket(
                external_id=external_id,
                url=_default_web_url(config, external_id),
                status_raw=None,
                status_normalized="unknown",
            )
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"OpenProject status fetch failed ({response.status_code})",
                status_code=response.status_code,
            )
        item = response.json()
        status_name = _extract_status_name(item)
        web_url = _extract_web_url(config, item, external_id)
        return ExternalTicket(
            external_id=external_id,
            url=web_url,
            status_raw=status_name,
            status_normalized=self.normalize_status(status_name, {}),
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

    def _request(self, method: str, url: str, secret: str, **kwargs):
        token = base64.b64encode(f"apikey:{secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        timeout = settings.INTEGRATION_HTTP_TIMEOUT_SECONDS
        try:
            with httpx.Client(timeout=timeout) as http:
                return http.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"OpenProject request failed: {exc}") from exc


def _extract_status_name(item: dict[str, Any]) -> str | None:
    if not isinstance(item, dict):
        return None
    embedded = item.get("_embedded") or {}
    status = embedded.get("status") if isinstance(embedded, dict) else None
    if isinstance(status, dict) and status.get("name"):
        return status["name"]
    links = item.get("_links") or {}
    link_status = links.get("status") if isinstance(links, dict) else None
    if isinstance(link_status, dict) and link_status.get("title"):
        return link_status["title"]
    return None


def _extract_web_url(config: dict[str, Any], item: dict[str, Any], external_id: str) -> str:
    if isinstance(item, dict):
        links = item.get("_links") or {}
        self_link = links.get("self") if isinstance(links, dict) else None
        if isinstance(self_link, dict) and self_link.get("href"):
            return _absolute(config, self_link["href"])
    return _default_web_url(config, external_id)


def _default_web_url(config: dict[str, Any], external_id: str) -> str:
    return f"{config['base_url']}/work_packages/{external_id}"


def _absolute(config: dict[str, Any], href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"{config['base_url']}{href}"


register_provider(OpenProjectProvider())
