import pytest
from pydantic import ValidationError

from testjam.core.config import PLACEHOLDER_SECRET_KEYS, Settings

RANDOM_SECRET_KEY = "3f9a1c0d7e5b2a4968c1f0e7d3b5a2c4"


def test_missing_secret_key_aborts_startup(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None)


@pytest.mark.parametrize("secret_key", sorted(PLACEHOLDER_SECRET_KEYS))
def test_placeholder_secret_key_aborts_startup(secret_key):
    with pytest.raises(ValidationError, match="openssl rand -hex 32"):
        Settings(SECRET_KEY=secret_key, _env_file=None)


def test_blank_secret_key_aborts_startup():
    with pytest.raises(ValidationError, match="openssl rand -hex 32"):
        Settings(SECRET_KEY="   ", _env_file=None)


def test_random_secret_key_is_accepted():
    settings = Settings(SECRET_KEY=RANDOM_SECRET_KEY, _env_file=None)

    assert settings.SECRET_KEY == RANDOM_SECRET_KEY
