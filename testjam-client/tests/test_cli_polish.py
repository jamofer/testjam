"""C.7 polish — status colors, pretty errors."""
from __future__ import annotations

import pytest

from testjam_client.cli import run_with_pretty_errors
from testjam_client.cli.colors import STATUS_STYLES, style_status
from testjam_client.errors import NotFound


def test_known_status_returns_markup():
    assert style_status("passed") == "[bold green]passed[/bold green]"
    assert style_status("failed") == "[bold red]failed[/bold red]"


def test_unknown_status_returns_plain_string():
    assert style_status("mystery") == "mystery"


def test_empty_status_returns_empty_string():
    assert style_status(None) == ""
    assert style_status("") == ""


def test_status_styles_cover_result_vocabulary():
    for status in ("passed", "failed", "blocked", "not_run", "running"):
        assert status in STATUS_STYLES


def test_status_styles_cover_execution_vocabulary():
    for status in ("pending", "in_progress", "completed", "aborted"):
        assert status in STATUS_STYLES


def test_testjam_error_is_caught_and_pretty_printed(capsys):
    def raises_testjam_error():
        raise NotFound("resource missing")

    with pytest.raises(SystemExit) as exit_info:
        run_with_pretty_errors(raises_testjam_error)

    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "Error" in combined
    assert "resource missing" in combined
    assert "Traceback" not in combined


def test_keyboard_interrupt_returns_130(capsys):
    def raises_interrupt():
        raise KeyboardInterrupt()

    with pytest.raises(SystemExit) as exit_info:
        run_with_pretty_errors(raises_interrupt)

    assert exit_info.value.code == 130


def test_non_testjam_exception_propagates(capsys):
    def raises_value_error():
        raise ValueError("not handled here")

    with pytest.raises(ValueError):
        run_with_pretty_errors(raises_value_error)
