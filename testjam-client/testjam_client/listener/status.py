"""Robot Framework → Testjam status translation."""
from __future__ import annotations

from testjam_client import statuses

RF_STATUS_MAP: dict[str, statuses.ResultStatus] = {
    "PASS": statuses.PASSED,
    "FAIL": statuses.FAILED,
    "SKIP": statuses.BLOCKED,
    "NOT RUN": statuses.NOT_RUN,
}


def map_rf_status(rf_status: str | None) -> statuses.ResultStatus:
    if not rf_status:
        return statuses.NOT_RUN
    return RF_STATUS_MAP.get(rf_status.upper(), statuses.NOT_RUN)
