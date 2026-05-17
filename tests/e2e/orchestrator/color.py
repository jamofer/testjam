"""Minimal ANSI colour helpers — only emit codes when stdout is a TTY."""
from __future__ import annotations

import os
import sys


_CODES = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}
_RESET = "\033[0m"


def supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if os.getenv("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def paint(text: str, style: str, *, enabled: bool = True) -> str:
    if not enabled:
        return text
    code = _CODES.get(style)
    if code is None:
        return text
    return f"{code}{text}{_RESET}"
