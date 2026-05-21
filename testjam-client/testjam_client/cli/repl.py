"""Interactive REPL — a `click-repl` wrapper.

Zero-arg ``testjam`` and the explicit ``testjam repl`` both funnel through
:func:`enter_repl`. The shell persists history at
``platformdirs.user_data_dir('testjam')/history``.
"""
from __future__ import annotations

from pathlib import Path

import click
import platformdirs
from click_repl import repl as _click_repl
from prompt_toolkit.history import FileHistory


PROMPT = "testjam> "
HISTORY_FILENAME = "history"


def enter_repl(context: click.Context) -> None:
    history_file = _history_path()
    history_file.parent.mkdir(parents=True, exist_ok=True)
    _click_repl(
        context,
        prompt_kwargs={
            "history": FileHistory(str(history_file)),
            "message": PROMPT,
        },
    )


def _history_path() -> Path:
    return Path(platformdirs.user_data_dir("testjam")) / HISTORY_FILENAME
