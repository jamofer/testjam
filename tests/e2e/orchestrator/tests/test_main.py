"""CLI behaviour: --list, filter narrowing, exit codes."""
from pathlib import Path

import pytest

from orchestrator import __main__ as cli
from orchestrator import runner
from orchestrator.discovery import Suite


@pytest.fixture
def suite_tree(tmp_path):
    (tmp_path / "api_server").mkdir()
    (tmp_path / "api_server" / "01_auth.robot").write_text("*** Test Cases ***\nT\n    Log    x\n")
    (tmp_path / "api_server" / "02_projects.robot").write_text("*** Test Cases ***\nT\n    Log    x\n")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "01_login.robot").write_text("*** Test Cases ***\nT\n    Log    x\n")
    return tmp_path


def test_list_mode_prints_every_discovered_suite(suite_tree, capsys):
    code = cli.main([str(suite_tree), "--list"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Api Server.01 Auth" in out
    assert "Api Server.02 Projects" in out
    assert "Frontend.01 Login" in out


def test_list_with_suite_filter_narrows_results(suite_tree, capsys):
    code = cli.main([str(suite_tree), "--list", "-s", "01 Auth"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Api Server.01 Auth" in out
    assert "02 Projects" not in out
    assert "Frontend.01 Login" not in out


def test_nested_pattern_filter_matches_longname(suite_tree, capsys):
    code = cli.main([str(suite_tree), "--list", "-s", "Api Server.*"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Api Server.01 Auth" in out
    assert "Api Server.02 Projects" in out
    assert "Frontend.01 Login" not in out


def test_returns_2_when_root_missing(tmp_path):
    assert cli.main([str(tmp_path / "missing")]) == 2


def test_exit_code_is_max_of_results(monkeypatch, suite_tree):
    def fake_pool(suites, **kwargs):
        return [
            runner.SuiteResult(suite=s, exit_code=2 if i else 0, duration_seconds=0.1, stdout_path=None)
            for i, s in enumerate(suites)
        ]

    monkeypatch.setattr(cli, "run_pool", fake_pool)

    code = cli.main([str(suite_tree), "-s", "*"])

    assert code == 2
