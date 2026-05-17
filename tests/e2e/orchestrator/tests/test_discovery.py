"""Discovery uses Robot's parser so the listener sees identical names."""
from pathlib import Path

from orchestrator.discovery import discover


def _write(path: Path, content: str = "*** Test Cases ***\nT\n    Log    x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_discover_collects_only_leaf_suites(tmp_path):
    _write(tmp_path / "api_server" / "01_auth.robot")
    _write(tmp_path / "api_server" / "02_projects.robot")
    _write(tmp_path / "frontend" / "01_login.robot")

    suites = discover(tmp_path)

    assert [s.longname for s in suites] == [
        "Api Server.01 Auth",
        "Api Server.02 Projects",
        "Frontend.01 Login",
    ]
    assert [s.leaf_name for s in suites] == ["01 Auth", "02 Projects", "01 Login"]


def test_discover_skips_directory_suites_without_tests(tmp_path):
    (tmp_path / "empty_dir").mkdir()
    _write(tmp_path / "api_server" / "01_auth.robot")

    suites = discover(tmp_path)

    assert [s.longname for s in suites] == ["Api Server.01 Auth"]
