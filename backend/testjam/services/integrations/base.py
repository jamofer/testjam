"""Provider protocol + shared types for external tracker integrations.

Concrete providers (``providers/github.py``, ``providers/jira.py``, …) inherit
``IntegrationProvider`` and call ``register_provider(MyProvider())`` at import
time. The HTTP layer only ever interacts with the abstract API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


NormalizedStatus = Literal["open", "closed", "unknown"]


class ProviderError(Exception):
    pass


class ProviderConfigError(ProviderError):
    pass


class ProviderRequestError(ProviderError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ExternalTicket:
    external_id: str
    url: str
    status_raw: str | None
    status_normalized: NormalizedStatus
    raw_payload: dict[str, Any] | None = None


class IntegrationProvider(Protocol):
    key: str
    label: str

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        ...

    def health_check(self, config: dict[str, Any], secret: str) -> None:
        ...

    def create_ticket(
        self,
        config: dict[str, Any],
        secret: str,
        *,
        title: str,
        body_markdown: str,
        labels: list[str] | None = None,
    ) -> ExternalTicket:
        ...

    def fetch_status(
        self,
        config: dict[str, Any],
        secret: str,
        external_id: str,
    ) -> ExternalTicket:
        ...

    def normalize_status(self, status_raw: str | None, status_mapping: dict[str, str]) -> NormalizedStatus:
        ...


_REGISTRY: dict[str, IntegrationProvider] = {}


def register_provider(provider: IntegrationProvider) -> None:
    _REGISTRY[provider.key] = provider


def get_provider(key: str) -> IntegrationProvider:
    if key not in _REGISTRY:
        raise ProviderConfigError(f"Unknown integration provider: {key!r}")
    return _REGISTRY[key]


def list_providers() -> list[IntegrationProvider]:
    return list(_REGISTRY.values())


def provider_keys() -> list[str]:
    return list(_REGISTRY.keys())
