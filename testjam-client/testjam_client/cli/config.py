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
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import platformdirs
import tomli_w


DEFAULT_PROFILE_NAME = "default"
CONFIG_FILE_NAME = "config.toml"
CONFIG_ENV_OVERRIDE = "TESTJAM_CONFIG"
SECRET_FIELDS: frozenset[str] = frozenset({"token", "api_key"})
EDITABLE_FIELDS: frozenset[str] = frozenset(
    {"url", "token", "api_key", "username", "default_project"}
)
FILE_PERMISSIONS = 0o600
DIRECTORY_PERMISSIONS = 0o700


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

    @property
    def profile_names(self) -> list[str]:
        return sorted(self._data.get("profiles", {}))

    def has_profile(self, name: str | None = None) -> bool:
        return (name or self.default_profile) in self._data.get("profiles", {})

    def profile(self, name: str | None = None) -> dict[str, Any]:
        """Read a profile; an unknown name reads as empty and is not created."""
        return dict(self._data.get("profiles", {}).get(name or self.default_profile, {}))

    def set_profile_value(self, name: str | None, key: str, value: str | None) -> None:
        profiles = self._data.setdefault("profiles", {})
        target = profiles.setdefault(name or self.default_profile, {})
        if value is None:
            target.pop(key, None)
            return
        target[key] = value

    def save(self) -> None:
        """Write the file atomically; it is never readable by others, not even briefly."""
        self.path.parent.mkdir(mode=DIRECTORY_PERMISSIONS, parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(dir=self.path.parent, prefix=f".{self.path.name}.")
        try:
            with os.fdopen(descriptor, "wb") as handle:
                tomli_w.dump(self._data, handle)
            os.chmod(temporary_path, FILE_PERMISSIONS)
            os.replace(temporary_path, self.path)
        except BaseException:
            Path(temporary_path).unlink(missing_ok=True)
            raise


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
