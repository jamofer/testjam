"""External tracker integrations.

Each provider implements ``IntegrationProvider`` and is registered via
``register_provider``. Provider modules add themselves on import — the
``providers`` submodule wires the concrete adapters.
"""
from testjam.services.integrations.base import (
    ExternalTicket,
    IntegrationProvider,
    NormalizedStatus,
    ProviderConfigError,
    ProviderError,
    ProviderRequestError,
    get_provider,
    list_providers,
    provider_keys,
    register_provider,
)
from testjam.services.integrations import providers  # noqa: F401 — registers adapters


__all__ = [
    "ExternalTicket",
    "IntegrationProvider",
    "NormalizedStatus",
    "ProviderConfigError",
    "ProviderError",
    "ProviderRequestError",
    "get_provider",
    "list_providers",
    "provider_keys",
    "register_provider",
]
