"""Run one Robot execution per suite with a bounded process pool.

Each worker invokes ``robot.run`` (Robot's own Python API) in an isolated
child process and feeds it a freshly-built ``TestjamListener`` instance. The
listener bootstraps the Testjam project + version + execution at
construction time, so passing the instance directly avoids Robot's dotted
listener import and keeps the orchestrator in control of how the listener is
configured.

Process isolation (instead of threads) is required because Robot maintains
module-level state that is not safe for concurrent in-process runs.
"""
from __future__ import annotations

import os
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import httpx
import robot

from orchestrator.discovery import Suite


SUITE_ADMIN_PASSWORD = "e2e-admin-pass"
SMTP_BASELINE = {
    "smtp_host": "mailpit",
    "smtp_port": 1025,
    "smtp_from": "noreply@testjam.test",
    "smtp_use_tls": False,
}


@dataclass(frozen=True)
class SuiteResult:
    suite: Suite
    exit_code: int
    duration_seconds: float
    stdout_path: Path | None


def run_pool(
    suites: list[Suite],
    *,
    root: Path,
    workers: int,
    base_env: dict[str, str],
    output_dir: Path,
    suite_filters: list[str] | None = None,
    test_filters: list[str] | None = None,
) -> list[SuiteResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[SuiteResult] = []
    if not suites:
        return results
    admins = _provision_suite_admins(suites, base_env)
    capped = max(1, min(workers, len(suites)))
    with ProcessPoolExecutor(max_workers=capped) as pool:
        futures = {
            pool.submit(
                _run_one, suite, str(root), base_env, str(output_dir),
                test_filters or [], admins.get(suite.longname),
            ): suite
            for suite in suites
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r.suite.longname)
    return results


def suite_admin_username(longname: str) -> str:
    """Stable per-suite admin username derived from the suite longname.

    Isolates notification inboxes between concurrent suites so assertions
    like ``I have 0 unread notifications`` cannot see other suites' events.
    """
    slug = re.sub(r"[^a-z0-9]+", "_", longname.lower()).strip("_")
    return f"e2e_{slug}"[:64]


def _provision_suite_admins(
    suites: list[Suite], base_env: dict[str, str],
) -> dict[str, dict[str, str]]:
    api_url = base_env.get("TESTJAM_API_URL")
    global_user = base_env.get("TESTJAM_USER")
    global_pass = base_env.get("TESTJAM_PASS")
    if not api_url or not global_user or not global_pass:
        return {}
    admins: dict[str, dict[str, str]] = {}
    with httpx.Client(base_url=api_url, timeout=15.0) as http:
        login = http.post(
            "/auth/login",
            data={"username": global_user, "password": global_pass},
        )
        login.raise_for_status()
        http.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        _configure_smtp_baseline(http)
        for suite in suites:
            username = suite_admin_username(suite.longname)
            user_id = _ensure_suite_admin(http, username)
            _wipe_suite_admin_projects(http, user_id)
            admins[suite.longname] = {
                "username": username,
                "password": SUITE_ADMIN_PASSWORD,
            }
    return admins


def _configure_smtp_baseline(http: httpx.Client) -> None:
    """Establish a stable SMTP=mailpit baseline once so suites can send mail
    without mutating the global settings row themselves. Avoids cross-suite
    races on `smtp_host`/`smtp_port`.
    """
    response = http.put("/settings", json=SMTP_BASELINE)
    response.raise_for_status()


def _ensure_suite_admin(http: httpx.Client, username: str) -> int:
    create = http.post("/users", json={
        "username": username,
        "email": f"{username}@e2e.local.example",
        "password": SUITE_ADMIN_PASSWORD,
    })
    if create.status_code == 201:
        user_id = create.json()["id"]
    elif create.status_code == 400 and "already exists" in create.text:
        listed = http.get("/users", params={"include_deleted": "true"}).json()
        existing = next(u for u in listed if u["username"] == username)
        user_id = existing["id"]
        if existing.get("deleted_at"):
            http.post(f"/users/{user_id}/restore")
    else:
        create.raise_for_status()
    update = http.put(f"/users/{user_id}", json={
        "is_admin": True,
        "is_active": True,
        "password": SUITE_ADMIN_PASSWORD,
        "clear_lockout": True,
    })
    update.raise_for_status()
    return user_id


def _wipe_suite_admin_projects(http: httpx.Client, user_id: int) -> None:
    """Delete stale projects from prior runs that the suite admin owns.

    Without this, accumulated projects from previous batches drown out the
    fresh-per-test ones (the command palette shows the top N projects, etc.).
    """
    listing = http.get("/projects", params={"include_archived": "true"}).json()
    for project in listing:
        if project.get("owner_id") == user_id:
            http.delete(f"/projects/{project['id']}")


def _run_one(
    suite: Suite,
    root: str,
    base_env: dict[str, str],
    output_dir: str,
    test_filters: list[str],
    suite_admin: dict[str, str] | None,
) -> SuiteResult:
    from testjam_listener import TestjamListener

    for key, value in base_env.items():
        os.environ[key] = value
    os.environ["TESTJAM_EXECUTION_TITLE"] = suite.longname
    if suite_admin is not None:
        os.environ["TESTJAM_USER"] = suite_admin["username"]
        os.environ["TESTJAM_PASS"] = suite_admin["password"]
        os.environ.pop("TESTJAM_TOKEN", None)

    suite_outdir = Path(output_dir) / _safe_directory(suite.longname)
    suite_outdir.mkdir(parents=True, exist_ok=True)
    stdout_path = suite_outdir / "robot.log"

    run_kwargs: dict = {
        "listener": TestjamListener(),
        "suite": suite.leaf_name,
        "outputdir": str(suite_outdir),
        "consolewidth": 120,
    }
    if test_filters:
        run_kwargs["test"] = test_filters

    started = time.monotonic()
    with open(stdout_path, "w") as stdout_file:
        run_kwargs["stdout"] = stdout_file
        run_kwargs["stderr"] = stdout_file
        exit_code = robot.run(root, **run_kwargs)
    duration = time.monotonic() - started
    return SuiteResult(
        suite=suite,
        exit_code=int(exit_code),
        duration_seconds=duration,
        stdout_path=stdout_path,
    )


def _safe_directory(name: str) -> str:
    return name.replace("/", "_").replace(" ", "_")
