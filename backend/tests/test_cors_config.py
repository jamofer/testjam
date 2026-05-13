"""CORS_ORIGINS env var parses into a list of allowed origins."""
import importlib

import pytest

from testjam.core import config as config_module


@pytest.fixture
def reload_settings(monkeypatch):
    def _reload(value: str | None) -> config_module.Settings:
        if value is None:
            monkeypatch.delenv("CORS_ORIGINS", raising=False)
        else:
            monkeypatch.setenv("CORS_ORIGINS", value)
        importlib.reload(config_module)
        return config_module.settings

    return _reload


def test_default_cors_origins_match_dev_localhost(reload_settings):
    settings = reload_settings(None)

    assert settings.cors_origins_list == [
        "http://localhost:5173",
        "http://localhost:3000",
    ]


def test_cors_origins_parsed_from_comma_separated_env(reload_settings):
    settings = reload_settings("https://app.example.com,https://admin.example.com")

    assert settings.cors_origins_list == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_cors_origins_strips_whitespace_and_drops_empty(reload_settings):
    settings = reload_settings(" https://a.example.com , , https://b.example.com ")

    assert settings.cors_origins_list == [
        "https://a.example.com",
        "https://b.example.com",
    ]
