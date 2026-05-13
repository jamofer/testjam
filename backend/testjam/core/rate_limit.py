import os

from slowapi import Limiter
from slowapi.util import get_remote_address

LOGIN_RATE_LIMIT = "5/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[])

# Allow ops + E2E to opt out without re-defining the decorators.
if os.environ.get("RATE_LIMIT_ENABLED", "true").strip().lower() in ("0", "false", "no", "off"):
    limiter.enabled = False
