"""Jira Cloud / Server REST v3 provider.

Auth: API token (Cloud) or PAT (Server/DC). Cloud uses Basic ``email:token``;
when the integration config carries an ``email`` field we encode that pair,
otherwise we fall back to ``Bearer <token>`` (Server/DC PAT).

Status mapping is workflow-specific in Jira (Done/In Review/Backlog/…), so
``status_mapping`` on the integration is honored verbatim. Defaults map
``Done`` to ``closed``; everything else falls through to ``open`` or
``unknown`` if the workflow uses an unfamiliar transition.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx

from testjam.core.config import settings
from testjam.services.integrations.base import (
    ExternalTicket,
    NormalizedStatus,
    ProviderConfigError,
    ProviderRequestError,
    register_provider,
)
from testjam.services.integrations.markdown_to_adf import to_adf


_DEFAULT_STATUS_MAPPING = {"Done": "closed"}
_CLOSED_TERMS = {"done", "closed", "resolved"}


class JiraProvider:
    key = "jira"
    label = "Jira"

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        base_url = (config.get("base_url") or "").strip().rstrip("/")
        project_key = (config.get("project_key") or "").strip()
        issue_type = (config.get("issue_type") or "Bug").strip()
        email = (config.get("email") or "").strip() or None
        if not base_url:
            raise ProviderConfigError("base_url is required (e.g. https://acme.atlassian.net)")
        if not project_key:
            raise ProviderConfigError("project_key is required")
        return {
            "base_url": base_url,
            "project_key": project_key,
            "issue_type": issue_type,
            "email": email,
        }

    def health_check(self, config: dict[str, Any], secret: str) -> None:
        if not secret:
            raise ProviderConfigError("API token is required")
        url = f"{config['base_url']}/rest/api/3/project/{config['project_key']}"
        response = self._request("GET", url, config, secret)
        if response.status_code == 404:
            raise ProviderConfigError("Jira project not found or token lacks access")
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Jira health check failed ({response.status_code})",
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
        url = f"{config['base_url']}/rest/api/3/issue"
        payload: dict[str, Any] = {
            "fields": {
                "project": {"key": config["project_key"]},
                "summary": title,
                "description": to_adf(body_markdown or ""),
                "issuetype": {"name": config.get("issue_type", "Bug")},
            }
        }
        if labels:
            payload["fields"]["labels"] = _safe_labels(labels)
        response = self._request("POST", url, config, secret, json=payload)
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Jira issue creation failed ({response.status_code}): {response.text[:200]}",
                status_code=response.status_code,
            )
        issue = response.json()
        key = issue.get("key")
        if not key:
            raise ProviderRequestError("Jira did not return an issue key")
        return ExternalTicket(
            external_id=key,
            url=f"{config['base_url']}/browse/{key}",
            status_raw=None,
            status_normalized="open",
            raw_payload=issue,
        )

    def fetch_status(
        self, config: dict[str, Any], secret: str, external_id: str,
    ) -> ExternalTicket:
        url = f"{config['base_url']}/rest/api/3/issue/{external_id}"
        response = self._request("GET", url, config, secret)
        if response.status_code == 404:
            return ExternalTicket(
                external_id=external_id,
                url=f"{config['base_url']}/browse/{external_id}",
                status_raw=None,
                status_normalized="unknown",
            )
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Jira status fetch failed ({response.status_code})",
                status_code=response.status_code,
            )
        body = response.json()
        status_raw = (
            body.get("fields", {}).get("status", {}).get("name")
            if isinstance(body, dict) else None
        )
        return ExternalTicket(
            external_id=external_id,
            url=f"{config['base_url']}/browse/{external_id}",
            status_raw=status_raw,
            status_normalized=self.normalize_status(status_raw, {}),
            raw_payload=body if isinstance(body, dict) else None,
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

    def _request(self, method: str, url: str, config: dict[str, Any], secret: str, **kwargs):
        headers = _auth_headers(config, secret)
        timeout = settings.INTEGRATION_HTTP_TIMEOUT_SECONDS
        try:
            with httpx.Client(timeout=timeout) as http:
                return http.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"Jira request failed: {exc}") from exc


def _auth_headers(config: dict[str, Any], secret: str) -> dict[str, str]:
    email = config.get("email")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if email:
        token = base64.b64encode(f"{email}:{secret}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    else:
        headers["Authorization"] = f"Bearer {secret}"
    return headers


def _safe_labels(labels: list[str]) -> list[str]:
    # Jira labels cannot contain spaces.
    out: list[str] = []
    for label in labels:
        clean = label.replace(" ", "-")
        if clean:
            out.append(clean)
    return out


register_provider(JiraProvider())
