"""Persistent CLI configuration stored at ``~/.config/testjam/config.toml``.

The store keeps one or more named profiles. Each profile bundles the server
URL, the cached JWT (after ``testjam login``), an optional project-scoped
``api_key``, and the username last logged in with — enough to make any
subsequent command unattended.

The file location can be overridden with ``TESTJAM_CONFIG`` for tests or
self-contained deployments.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

import platformdirs
import tomli_w


DEFAULT_PROFILE_NAME = "default"
CONFIG_FILE_NAME = "config.toml"
CONFIG_ENV_OVERRIDE = "TESTJAM_CONFIG"
SECRET_FIELDS: frozenset[str] = frozenset({"token", "api_key"})
EDITABLE_FIELDS: frozenset[str] = frozenset({"url", "token", "api_key", "username"})
FILE_PERMISSIONS = 0o600


class ConfigStore:
    """Load + mutate + persist the user's TOML config file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, Any] = {}
        if path.exists():
            with path.open("rb") as handle:
                self._data = tomllib.load(handle)

    @property
    def default_profile(self) -> str:
        return self._data.get("default_profile", DEFAULT_PROFILE_NAME)

    def profile(self, name: str | None = None) -> dict[str, Any]:
        resolved_name = name or self.default_profile
        profiles = self._data.setdefault("profiles", {})
        return profiles.setdefault(resolved_name, {})

    def set_profile_value(self, name: str | None, key: str, value: str | None) -> None:
        target = self.profile(name)
        if value is None:
            target.pop(key, None)
            return
        target[key] = value

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("wb") as handle:
            tomli_w.dump(self._data, handle)
        os.chmod(self.path, FILE_PERMISSIONS)


def default_config_path() -> Path:
    override = os.environ.get(CONFIG_ENV_OVERRIDE)
    if override:
        return Path(override)
    return Path(platformdirs.user_config_dir("testjam")) / CONFIG_FILE_NAME


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-4:]}"
