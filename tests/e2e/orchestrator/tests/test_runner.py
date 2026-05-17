"""Unit tests for the runner helpers.

Full ``run_pool`` is exercised via ``test_main.py`` which monkeypatches it —
testing the pool plumbing directly would require a fake ``robot.run`` and
``TestjamListener`` shipped across the process boundary, which is more
machinery than the trivial wiring warrants.
"""
from pathlib import Path

from orchestrator import runner
from orchestrator.discovery import Suite


def test_run_pool_returns_empty_for_no_suites(tmp_path):
    assert runner.run_pool(
        [], root=tmp_path, workers=4, base_env={}, output_dir=tmp_path / "out",
    ) == []


def test_safe_directory_replaces_path_separators_and_spaces():
    assert runner._safe_directory("Api Server.01 Auth") == "Api_Server.01_Auth"
    assert runner._safe_directory("a/b c") == "a_b_c"


def test_suite_result_is_immutable():
    result = runner.SuiteResult(
        suite=Suite(path=Path("/x.robot"), leaf_name="X", longname="X"),
        exit_code=0,
        duration_seconds=1.0,
        stdout_path=None,
    )
    try:
        result.exit_code = 1  # type: ignore[misc]
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("SuiteResult should be frozen")
