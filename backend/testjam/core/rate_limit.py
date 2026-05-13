from slowapi import Limiter
from slowapi.util import get_remote_address

LOGIN_RATE_LIMIT = "5/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[])
