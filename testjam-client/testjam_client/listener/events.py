"""Plain copies of the Robot objects the reporter reads.

Robot keeps mutating its model and result objects after a listener method
returns, and they are not meant to be read from another thread, so every event
is copied on Robot's thread before it is queued. Timestamps are taken at copy
time too, so a busy queue does not shift them.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SuiteEvent:
    name: str
    source: str | None
    description: str | None

    @classmethod
    def from_robot(cls, data: Any) -> SuiteEvent:
        source = getattr(data, "source", None)
        return cls(
            name=data.name,
            source=str(source) if source else None,
            description=_description(data),
        )


@dataclass(frozen=True)
class StepEvent:
    action: str
    step_type: str


@dataclass(frozen=True)
class TestEvent:
    __test__ = False

    name: str
    description: str | None
    tags: tuple[str, ...]
    steps: tuple[StepEvent, ...]
    started_at: str

    @classmethod
    def from_robot(cls, data: Any) -> TestEvent:
        return cls(
            name=data.name,
            description=_description(data),
            tags=tuple(str(tag) for tag in getattr(data, "tags", [])),
            steps=tuple(_steps(data)),
            started_at=now_isoformat(),
        )


@dataclass(frozen=True)
class OutcomeEvent:
    status: str
    duration_ms: int | None
    message: str
    finished_at: str

    @classmethod
    def from_robot(cls, result: Any) -> OutcomeEvent:
        elapsed = getattr(result, "elapsedtime", None)
        return cls(
            status=str(getattr(result, "status", "")),
            duration_ms=int(elapsed) if elapsed is not None else None,
            message=str(getattr(result, "message", "") or ""),
            finished_at=now_isoformat(),
        )


@dataclass(frozen=True)
class LogEvent:
    level: str
    message: str
    timestamp: Any

    @classmethod
    def from_robot(cls, message: Any) -> LogEvent:
        return cls(
            level=getattr(message, "level", "INFO"),
            message=getattr(message, "message", ""),
            timestamp=getattr(message, "timestamp", None),
        )


def now_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat()


def _description(data: Any) -> str | None:
    return (getattr(data, "doc", None) or "").strip() or None


def _steps(data: Any) -> list[StepEvent]:
    steps: list[StepEvent] = []
    setup = getattr(data, "setup", None)
    if setup and getattr(setup, "name", None):
        steps.append(StepEvent(action=setup.name, step_type="setup"))
    for item in getattr(data, "body", []):
        item_type = getattr(item, "type", "KEYWORD")
        action = getattr(item, "name", None) or f"[{item_type}]"
        step_type = "teardown" if item_type == "TEARDOWN" else "action"
        steps.append(StepEvent(action=action, step_type=step_type))
    teardown = getattr(data, "teardown", None)
    if teardown and getattr(teardown, "name", None):
        steps.append(StepEvent(action=teardown.name, step_type="teardown"))
    return steps
