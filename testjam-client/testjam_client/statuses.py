"""Status values the Testjam API accepts and returns."""
from __future__ import annotations

from typing import Literal

ResultStatus = Literal["not_run", "running", "passed", "failed", "blocked"]
ExecutionStatus = Literal["pending", "in_progress", "completed", "aborted"]

NOT_RUN: ResultStatus = "not_run"
RUNNING: ResultStatus = "running"
PASSED: ResultStatus = "passed"
FAILED: ResultStatus = "failed"
BLOCKED: ResultStatus = "blocked"

PENDING: ExecutionStatus = "pending"
IN_PROGRESS: ExecutionStatus = "in_progress"
COMPLETED: ExecutionStatus = "completed"
ABORTED: ExecutionStatus = "aborted"

TERMINAL_EXECUTION_STATUSES: frozenset[ExecutionStatus] = frozenset({COMPLETED, ABORTED})
UNSUCCESSFUL_RESULT_STATUSES: frozenset[ResultStatus] = frozenset({FAILED, BLOCKED})
