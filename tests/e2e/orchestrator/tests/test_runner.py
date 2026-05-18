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


def test_suite_admin_username_is_stable_and_slugified():
    assert runner.suite_admin_username("Api Server.11 Notifications") == "e2e_api_server_11_notifications"
    assert runner.suite_admin_username("Frontend.07 Execution Run") == "e2e_frontend_07_execution_run"
    assert runner.suite_admin_username("Api Server.11 Notifications") == "e2e_api_server_11_notifications"


def test_suite_admin_username_truncates_long_names():
    assert len(runner.suite_admin_username("X" * 200)) <= 64


def test_provision_suite_admins_skips_when_creds_missing():
    suites = [Suite(path=Path("/x.robot"), leaf_name="X", longname="X")]

    assert runner._provision_suite_admins(suites, {}) == {}
    assert runner._provision_suite_admins(suites, {"TESTJAM_API_URL": "http://x"}) == {}


def test_provision_suite_admins_creates_and_reuses(monkeypatch):
    suites = [
        Suite(path=Path("/a.robot"), leaf_name="A", longname="Api Server.11 Notifications"),
        Suite(path=Path("/b.robot"), leaf_name="B", longname="Frontend.09 Notifications"),
    ]
    base_env = {
        "TESTJAM_API_URL": "http://api",
        "TESTJAM_USER": "admin",
        "TESTJAM_PASS": "admin123",
    }
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(runner.httpx, "Client", lambda *a, **kw: _FakeHttpClient(calls))

    first = runner._provision_suite_admins(suites, base_env)
    second = runner._provision_suite_admins(suites, base_env)

    assert set(first) == {s.longname for s in suites}
    assert first["Api Server.11 Notifications"]["username"] == "e2e_api_server_11_notifications"
    assert all(a["password"] == runner.SUITE_ADMIN_PASSWORD for a in first.values())
    assert second == first
    create_attempts = [path for method, path in calls if method == "POST" and path == "/users"]
    assert len(create_attempts) == 4


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


class _FakeResponse:
    def __init__(self, status_code, body=None, text=""):
        self.status_code = status_code
        self._body = body
        self.text = text

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}: {self.text}")


class _FakeHttpClient:
    def __init__(self, calls):
        self.headers = {}
        self._calls = calls
        self._users_by_name = {}
        self._next_id = 1

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def post(self, path, json=None, data=None, params=None):
        self._calls.append(("POST", path))
        if path == "/auth/login":
            return _FakeResponse(200, {"access_token": "tok"})
        if path == "/users":
            username = json["username"]
            if username in self._users_by_name:
                return _FakeResponse(400, text=f"User '{username}' already exists")
            self._users_by_name[username] = self._next_id
            self._next_id += 1
            return _FakeResponse(201, {"id": self._users_by_name[username]})
        raise AssertionError(f"unexpected POST {path}")

    def get(self, path, params=None):
        self._calls.append(("GET", path))
        if path == "/users":
            return _FakeResponse(200, [
                {"username": user, "id": uid, "deleted_at": None}
                for user, uid in self._users_by_name.items()
            ])
        if path == "/projects":
            return _FakeResponse(200, [])
        raise AssertionError(f"unexpected GET {path}")

    def put(self, path, json=None):
        self._calls.append(("PUT", path))
        return _FakeResponse(200, {})
