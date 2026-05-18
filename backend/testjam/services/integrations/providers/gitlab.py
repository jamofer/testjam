"""GitLab Issues provider.

Auth: PAT with ``api`` scope. Sent via the ``PRIVATE-TOKEN`` header (also the
documented form for project access tokens).

Project addressing: either numeric project id or the URL-encoded full path
(``owner/repo``). We always URL-encode the value to be safe.

Base URL: ``https://gitlab.com`` by default; override for self-hosted.
"""
from __future__ import annotations

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


_DEFAULT_BASE_URL = "https://gitlab.com"
_DEFAULT_STATUS_MAPPING = {"opened": "open", "closed": "closed"}


class GitLabProvider:
    key = "gitlab"
    label = "GitLab Issues"

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        project = (config.get("project") or "").strip()
        if not project:
            raise ProviderConfigError("project is required (numeric id or 'owner/repo')")
        base_url = (config.get("base_url") or _DEFAULT_BASE_URL).strip().rstrip("/")
        return {"project": project, "base_url": base_url}

    def health_check(self, config: dict[str, Any], secret: str) -> None:
        if not secret:
            raise ProviderConfigError("API token is required")
        url = f"{self._project_url(config)}"
        response = self._request("GET", url, secret)
        if response.status_code == 404:
            raise ProviderConfigError("GitLab project not found or token lacks access")
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"GitLab health check failed ({response.status_code})",
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
        url = f"{self._project_url(config)}/issues"
        payload: dict[str, Any] = {"title": title, "description": body_markdown or ""}
        if labels:
            payload["labels"] = ",".join(label.strip() for label in labels if label.strip())
        response = self._request("POST", url, secret, json=payload)
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"GitLab issue creation failed ({response.status_code}): {response.text[:200]}",
                status_code=response.status_code,
            )
        issue = response.json()
        iid = issue.get("iid")
        if iid is None:
            raise ProviderRequestError("GitLab did not return an issue iid")
        return ExternalTicket(
            external_id=str(iid),
            url=issue.get("web_url", self._issue_url(config, str(iid))),
            status_raw=issue.get("state"),
            status_normalized=self.normalize_status(issue.get("state"), {}),
            raw_payload=issue,
        )

    def fetch_status(
        self, config: dict[str, Any], secret: str, external_id: str,
    ) -> ExternalTicket:
        url = f"{self._project_url(config)}/issues/{external_id}"
        response = self._request("GET", url, secret)
        if response.status_code == 404:
            return ExternalTicket(
                external_id=external_id,
                url=self._issue_url(config, external_id),
                status_raw=None,
                status_normalized="unknown",
            )
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"GitLab status fetch failed ({response.status_code})",
                status_code=response.status_code,
            )
        issue = response.json()
        state = issue.get("state")
        return ExternalTicket(
            external_id=external_id,
            url=issue.get("web_url", self._issue_url(config, external_id)),
            status_raw=state,
            status_normalized=self.normalize_status(state, {}),
            raw_payload=issue,
        )

    def normalize_status(
        self, status_raw: str | None, status_mapping: dict[str, str],
    ) -> NormalizedStatus:
        if status_raw is None:
            return "unknown"
        merged = {**_DEFAULT_STATUS_MAPPING, **status_mapping}
        value = merged.get(status_raw, "unknown")
        if value not in ("open", "closed", "unknown"):
            return "unknown"
        return value  # type: ignore[return-value]

    def _project_url(self, config: dict[str, Any]) -> str:
        encoded = quote(config["project"], safe="")
        return f"{config['base_url']}/api/v4/projects/{encoded}"

    def _issue_url(self, config: dict[str, Any], external_id: str) -> str:
        return f"{config['base_url']}/{config['project']}/-/issues/{external_id}"

    def _request(self, method: str, url: str, secret: str, **kwargs):
        headers = {
            "PRIVATE-TOKEN": secret,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        timeout = settings.INTEGRATION_HTTP_TIMEOUT_SECONDS
        try:
            with httpx.Client(timeout=timeout) as http:
                return http.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"GitLab request failed: {exc}") from exc


register_provider(GitLabProvider())
