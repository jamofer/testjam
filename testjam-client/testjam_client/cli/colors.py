"""Status → Rich style map.

Mirrors ``frontend/src/lib/statusConfig.js`` for result statuses
(passed/failed/blocked/not_run/running) and extends with the execution and
bug status vocabularies the CLI also has to render.

Rich's ``Console`` already honours ``NO_COLOR`` automatically, so callers do
not need to gate styling themselves — when colour is off the markup
collapses to plain text.
"""
from __future__ import annotations


STATUS_STYLES: dict[str, str] = {
    "passed": "bold green",
    "failed": "bold red",
    "blocked": "bold yellow",
    "not_run": "dim",
    "running": "bold blue",
    "pending": "dim",
    "in_progress": "bold blue",
    "completed": "bold green",
    "aborted": "bold red",
    "open": "bold red",
    "resolved": "bold green",
    "closed": "dim",
}


def style_status(status: str | None) -> str:
    if not status:
        return ""
    rich_style = STATUS_STYLES.get(status)
    if not rich_style:
        return status
    return f"[{rich_style}]{status}[/{rich_style}]"
