"""Concrete integration provider adapters.

Importing this package triggers each adapter to call ``register_provider``.
Concrete adapters land in later phases (F1 GitHub, F2 Jira, …); F0 ships a
deterministic in-process ``fake`` provider so the scaffold + tests are
self-contained.
"""
from testjam.services.integrations.providers import (  # noqa: F401
    azure_devops, fake, github, gitlab, jira,
)


__all__ = ["azure_devops", "fake", "github", "gitlab", "jira"]
