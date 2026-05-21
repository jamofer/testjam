"""Shared CLI runtime state.

The root Typer callback builds a :class:`CliState` and attaches it to the
``typer.Context.obj`` so every subcommand can pull the active profile, the
config store, and any per-invocation overrides (``--api-key`` for one-shot
runs) from a single object.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from testjam_client.cli.config import ConfigStore


@dataclass
class CliState:
    config: ConfigStore
    profile_name: str
    api_key_override: str | None = None

    @property
    def profile(self) -> dict[str, Any]:
        return self.config.profile(self.profile_name)
