"""Retry an assertion until the server catches up with the UI."""
import time

PERSISTENCE_TIMEOUT_SECONDS = 5.0
POLL_INTERVAL_SECONDS = 0.2


def eventually(check, timeout: float = PERSISTENCE_TIMEOUT_SECONDS) -> None:
    """Call ``check`` until it stops raising ``AssertionError`` or time runs out."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            check()
            return
        except AssertionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(POLL_INTERVAL_SECONDS)
