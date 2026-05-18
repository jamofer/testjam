"""Concrete integration provider adapters.

Importing this package triggers each adapter to call ``register_provider``.
Concrete adapters land in later phases (F1 GitHub, F2 Jira, …); F0 ships a
deterministic in-process ``fake`` provider so the scaffold + tests are
self-contained.
"""
from testjam.services.integrations.providers import fake, github, jira  # noqa: F401


__all__ = ["fake", "github", "jira"]
