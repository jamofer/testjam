"""Locate Robot Framework leaf suites via Robot's own parser.

Using ``robot.api.TestSuiteBuilder`` defers every quirk of suite naming
(``__init__.robot`` metadata, ``Name`` setting overrides, underscore
conversion) to Robot itself, so the longname seen by the orchestrator always
matches what the listener observes at runtime.

A leaf suite is one that contains tests directly. Directory wrappers are
skipped — the orchestrator launches a Robot subprocess per leaf so each
Testjam execution corresponds to exactly one ``.robot`` file's tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from robot.api import TestSuiteBuilder


@dataclass(frozen=True)
class Suite:
    path: Path
    """Path to the ``.robot`` file."""

    leaf_name: str
    """Suite name Robot assigns to this file (e.g. ``"01 Auth"``)."""

    longname: str
    """Dotted Robot longname relative to the discovery root, excluding the
    synthetic top-level wrapper (e.g. ``"Api Server.01 Auth"``)."""


def discover(root: Path) -> list[Suite]:
    root = root.resolve()
    parsed = TestSuiteBuilder().build(str(root))
    suites: list[Suite] = []
    _collect(parsed, suites, prefix=())
    suites.sort(key=lambda s: s.longname)
    return suites


def _collect(node, out: list[Suite], prefix: tuple[str, ...]) -> None:
    if node.tests:
        relative = prefix + (node.name,)
        out.append(Suite(
            path=Path(node.source),
            leaf_name=node.name,
            longname=".".join(relative[1:]) if len(relative) > 1 else relative[0],
        ))
        return
    for child in node.suites:
        _collect(child, out, prefix + (node.name,))
