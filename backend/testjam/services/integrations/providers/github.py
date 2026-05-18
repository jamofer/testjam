"""GitHub Issues provider.

Auth: PAT (classic or fine-grained) with ``repo`` or ``Issues: write`` scope.
Config: ``owner``, ``repo`` (slash form ``owner/repo`` also accepted).
Base URL is configurable for GitHub Enterprise via ``api_base`` (default
``https://api.github.com``).
"""
from __future__ import annotations

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


_DEFAULT_API_BASE = "https://api.github.com"
_DEFAULT_STATUS_MAPPING = {"open": "open", "closed": "closed"}


class GitHubProvider:
    key = "github"
    label = "GitHub Issues"

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        owner = config.get("owner")
        repo = config.get("repo")
        slug = config.get("repository")
        if slug and not owner and not repo:
            if "/" not in slug:
                raise ProviderConfigError("repository must be in 'owner/repo' form")
            owner, _, repo = slug.partition("/")
        if not owner:
            raise ProviderConfigError("owner is required")
        if not repo:
            raise ProviderConfigError("repo is required")
        api_base = config.get("api_base") or _DEFAULT_API_BASE
        return {
            "owner": str(owner).strip(),
            "repo": str(repo).strip(),
            "api_base": api_base.rstrip("/"),
        }

    def health_check(self, config: dict[str, Any], secret: str) -> None:
        if not secret:
            raise ProviderConfigError("API token is required")
        url = self._repo_url(config)
        response = self._request("GET", url, secret)
        if response.status_code == 404:
            raise ProviderConfigError("Repository not found or token lacks access")
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"GitHub health check failed ({response.status_code})",
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
        url = f"{self._repo_url(config)}/issues"
        payload: dict[str, Any] = {"title": title, "body": body_markdown or ""}
        if labels:
            payload["labels"] = labels
        response = self._request("POST", url, secret, json=payload)
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"GitHub issue creation failed ({response.status_code}): {response.text[:200]}",
                status_code=response.status_code,
            )
        issue = response.json()
        return ExternalTicket(
            external_id=str(issue["number"]),
            url=issue["html_url"],
            status_raw=issue.get("state"),
            status_normalized=self.normalize_status(issue.get("state"), {}),
            raw_payload=issue,
        )

    def fetch_status(
        self, config: dict[str, Any], secret: str, external_id: str,
    ) -> ExternalTicket:
        url = f"{self._repo_url(config)}/issues/{external_id}"
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
                f"GitHub status fetch failed ({response.status_code})",
                status_code=response.status_code,
            )
        issue = response.json()
        state = issue.get("state")
        return ExternalTicket(
            external_id=external_id,
            url=issue.get("html_url", self._issue_url(config, external_id)),
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

    def _repo_url(self, config: dict[str, Any]) -> str:
        base = config.get("api_base", _DEFAULT_API_BASE).rstrip("/")
        return f"{base}/repos/{config['owner']}/{config['repo']}"

    def _issue_url(self, config: dict[str, Any], external_id: str) -> str:
        # Best-effort HTML URL when GitHub didn't respond with one.
        return f"https://github.com/{config['owner']}/{config['repo']}/issues/{external_id}"

    def _request(self, method: str, url: str, secret: str, **kwargs):
        headers = {
            "Authorization": f"Bearer {secret}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        timeout = settings.INTEGRATION_HTTP_TIMEOUT_SECONDS
        try:
            with httpx.Client(timeout=timeout) as http:
                return http.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"GitHub request failed: {exc}") from exc


register_provider(GitHubProvider())
