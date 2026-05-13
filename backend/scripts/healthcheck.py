#!/usr/bin/env python
"""
Container healthcheck. Pings the /health endpoint locally and exits 0 if the
app reports healthy (200), 1 otherwise. Used by docker-compose healthcheck.
"""
import sys
import urllib.error
import urllib.request

HEALTH_URL = "http://localhost:8000/health"
TIMEOUT_SECONDS = 5


def main() -> int:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=TIMEOUT_SECONDS) as response:
            return 0 if response.status == 200 else 1
    except (urllib.error.URLError, OSError):
        return 1


if __name__ == "__main__":
    sys.exit(main())
