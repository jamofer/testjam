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
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import robot

from orchestrator.discovery import Suite


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
    capped = max(1, min(workers, len(suites)))
    with ProcessPoolExecutor(max_workers=capped) as pool:
        futures = {
            pool.submit(
                _run_one, suite, str(root), base_env, str(output_dir),
                test_filters or [],
            ): suite
            for suite in suites
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r.suite.longname)
    return results


def _run_one(
    suite: Suite,
    root: str,
    base_env: dict[str, str],
    output_dir: str,
    test_filters: list[str],
) -> SuiteResult:
    from testjam_listener import TestjamListener

    for key, value in base_env.items():
        os.environ[key] = value
    os.environ["TESTJAM_EXECUTION_TITLE"] = suite.longname

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
