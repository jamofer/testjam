"""In-process fake provider used by F0 scaffold + tests.

Real providers (F1+) replace this with HTTP-backed adapters. The fake stores
tickets in a process-local dict so tests can assert on push/sync behavior
without external network calls.
"""
from __future__ import annotations

import itertools
from typing import Any

from testjam.services.integrations.base import (
    ExternalTicket,
    IntegrationProvider,
    NormalizedStatus,
    ProviderConfigError,
    register_provider,
)


_DEFAULT_STATUS_MAPPING = {"Open": "open", "Closed": "closed"}


class FakeProvider:
    key = "fake"
    label = "Fake (for tests)"

    def __init__(self) -> None:
        self._tickets: dict[str, dict[str, Any]] = {}
        self._counter = itertools.count(1)

    def reset(self) -> None:
        self._tickets.clear()
        self._counter = itertools.count(1)

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        if "project_key" not in config:
            raise ProviderConfigError("project_key is required")
        return {"project_key": str(config["project_key"])}

    def health_check(self, config: dict[str, Any], secret: str) -> None:
        if not secret:
            raise ProviderConfigError("Secret is required")
        self.validate_config(config)

    def create_ticket(
        self,
        config: dict[str, Any],
        secret: str,
        *,
        title: str,
        body_markdown: str,
        labels: list[str] | None = None,
    ) -> ExternalTicket:
        self.health_check(config, secret)
        external_id = f"{config['project_key']}-{next(self._counter)}"
        ticket = {
            "external_id": external_id,
            "title": title,
            "body": body_markdown,
            "labels": list(labels or []),
            "status_raw": "Open",
        }
        self._tickets[external_id] = ticket
        return ExternalTicket(
            external_id=external_id,
            url=f"https://fake.example/tickets/{external_id}",
            status_raw="Open",
            status_normalized="open",
            raw_payload=ticket,
        )

    def fetch_status(
        self, config: dict[str, Any], secret: str, external_id: str,
    ) -> ExternalTicket:
        self.health_check(config, secret)
        ticket = self._tickets.get(external_id)
        if ticket is None:
            return ExternalTicket(
                external_id=external_id,
                url=f"https://fake.example/tickets/{external_id}",
                status_raw=None,
                status_normalized="unknown",
            )
        status_raw = ticket["status_raw"]
        normalized = self.normalize_status(status_raw, _DEFAULT_STATUS_MAPPING)
        return ExternalTicket(
            external_id=external_id,
            url=f"https://fake.example/tickets/{external_id}",
            status_raw=status_raw,
            status_normalized=normalized,
            raw_payload=ticket,
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

    def set_remote_status(self, external_id: str, status_raw: str) -> None:
        """Test helper — pretend the upstream tracker moved the ticket."""
        if external_id in self._tickets:
            self._tickets[external_id]["status_raw"] = status_raw


_INSTANCE = FakeProvider()
register_provider(_INSTANCE)


def instance() -> FakeProvider:
    return _INSTANCE
