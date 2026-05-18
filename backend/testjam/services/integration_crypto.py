"""Symmetric encryption for integration credentials at rest.

The Fernet key lives in ``settings.INTEGRATION_ENCRYPTION_KEY`` (env
``INTEGRATION_ENCRYPTION_KEY``). When missing, ``encrypt`` and ``decrypt``
raise ``IntegrationEncryptionUnavailable`` so the API surface can return
503 with a clear message instead of silently corrupting data.
"""
from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from testjam.core.config import settings


class IntegrationEncryptionUnavailable(RuntimeError):
    pass


class IntegrationDecryptError(RuntimeError):
    pass


def is_available() -> bool:
    return bool(settings.INTEGRATION_ENCRYPTION_KEY)


def encrypt(secret: str) -> bytes:
    return _cipher().encrypt(secret.encode("utf-8"))


def decrypt(token: bytes) -> str:
    try:
        return _cipher().decrypt(token).decode("utf-8")
    except InvalidToken as exc:
        raise IntegrationDecryptError("Stored credential is unreadable") from exc


@lru_cache(maxsize=1)
def _cipher() -> Fernet:
    key = settings.INTEGRATION_ENCRYPTION_KEY
    if not key:
        raise IntegrationEncryptionUnavailable(
            "INTEGRATION_ENCRYPTION_KEY is not configured",
        )
    return Fernet(key.encode("utf-8"))
