"""Robot Framework → Testjam status translation."""
from __future__ import annotations

RF_STATUS_MAP: dict[str, str] = {
    "PASS": "passed",
    "FAIL": "failed",
    "SKIP": "blocked",
    "NOT RUN": "not_run",
}


def map_rf_status(rf_status: str | None) -> str:
    if not rf_status:
        return "not_run"
    return RF_STATUS_MAP.get(rf_status.upper(), "not_run")
