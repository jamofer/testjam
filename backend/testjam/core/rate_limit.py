import os

from slowapi import Limiter
from starlette.requests import Request

from testjam.core.config import settings

LOGIN_RATE_LIMIT = "5/minute"
IMPORT_RATE_LIMIT = "30/minute"
EXPORT_RATE_LIMIT = "10/minute"
BACKUP_RATE_LIMIT = "3/minute"
FORWARDED_FOR_HEADER = "x-forwarded-for"
IN_MEMORY_STORAGE = "memory://"
UNKNOWN_CLIENT = "unknown"


def client_ip(request: Request) -> str | None:
    """Return the address seen by the outermost trusted proxy.

    Each proxy appends the address it received the request from, so entries
    left of the trusted ones are whatever the client chose to send.
    """
    forwarded = [
        address.strip()
        for address in request.headers.get(FORWARDED_FOR_HEADER, "").split(",")
        if address.strip()
    ]
    if 0 < settings.TRUSTED_PROXY_COUNT <= len(forwarded):
        return forwarded[-settings.TRUSTED_PROXY_COUNT]
    return request.client.host if request.client else None


def _rate_limit_key(request: Request) -> str:
    return client_ip(request) or UNKNOWN_CLIENT


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[],
    storage_uri=settings.REDIS_URL or IN_MEMORY_STORAGE,
    in_memory_fallback_enabled=True,
)

# Allow ops + E2E to opt out without re-defining the decorators.
if os.environ.get("RATE_LIMIT_ENABLED", "true").strip().lower() in ("0", "false", "no", "off"):
    limiter.enabled = False
