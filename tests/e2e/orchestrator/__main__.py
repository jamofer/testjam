"""CLI entrypoint: ``python -m orchestrator [options] [root]``.

Filters accepted by Robot itself (``--suite``/``--test`` glob patterns) are
applied twice:

- Against the discovered leaf longnames so the orchestrator only spawns a
  subprocess per matching suite.
- Pass-through to ``robot.run`` so each subprocess applies the same filter
  (relevant for ``--test`` where a leaf suite contains many tests).
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from pathlib import Path

from orchestrator.color import paint, supports_color
from orchestrator.discovery import discover
from orchestrator.runner import SuiteResult, run_pool


DEFAULT_OUTPUT_DIR = "results"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Launch one Robot execution per suite in parallel against Testjam.",
    )
    parser.add_argument("root", nargs="?", default="suites", help="Suite root directory")
    parser.add_argument("--workers", type=int, default=int(os.getenv("ORCHESTRATOR_WORKERS", "4")))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Robot output directory base")
    parser.add_argument(
        "-s", "--suite", action="append", default=[],
        help="Robot suite name or pattern (e.g. '01 Auth' or '*.Api Server.*'). Repeatable.",
    )
    parser.add_argument(
        "-t", "--test", action="append", default=[],
        help="Robot test name or pattern (e.g. 'Successful*'). Repeatable.",
    )
    parser.add_argument("--list", action="store_true", help="Print discovered suites and exit")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"orchestrator: root not found: {root}", file=sys.stderr)
        return 2

    suites = discover(root)
    if args.suite:
        suites = [s for s in suites if _matches_any(s.longname, s.leaf_name, args.suite)]
    if not suites:
        print(f"orchestrator: no suites under {root} match the given filters", file=sys.stderr)
        return 0

    if args.list:
        for suite in suites:
            print(f"{suite.longname}\t{suite.path}")
        return 0

    base_env = {k: v for k, v in os.environ.items() if k.startswith("TESTJAM_")}
    output_dir = Path(args.output_dir).resolve()
    color = supports_color()
    print(
        f">>> orchestrator: {len(suites)} suite(s), workers={args.workers}, "
        f"version={base_env.get('TESTJAM_VERSION') or '(none)'}, output={output_dir}",
    )

    results = run_pool(
        suites, root=root, workers=args.workers,
        base_env=base_env, output_dir=output_dir,
        suite_filters=args.suite, test_filters=args.test,
    )

    _print_summary(results, color=color)
    return max((r.exit_code for r in results), default=0)


def _matches_any(longname: str, leaf: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if "." in pattern or "*" in pattern:
            if fnmatch.fnmatchcase(longname, pattern):
                return True
        if fnmatch.fnmatchcase(leaf, pattern):
            return True
    return False


def _print_summary(results: list[SuiteResult], *, color: bool) -> None:
    if not results:
        return
    longest = max(len(r.suite.longname) for r in results)
    header = f"{'SUITE':<{longest}}  {'STATUS':<6}  {'TIME':>7}  EXIT"
    print()
    print(header)
    print("-" * len(header))
    for result in results:
        ok = result.exit_code == 0
        status = paint("ok" if ok else "FAIL", "green" if ok else "red", enabled=color)
        print(
            f"{result.suite.longname:<{longest}}  {status:<{6 + (len(status) - 6 if color else 0)}}  "
            f"{result.duration_seconds:>6.1f}s  {result.exit_code}",
        )
    failed = [r for r in results if r.exit_code != 0]
    print()
    total = paint(f"{len(results)} suite(s)", "bold", enabled=color)
    summary_count = paint(str(len(failed)), "red" if failed else "green", enabled=color)
    print(f"{total} · {summary_count} failed")
    for result in failed:
        if result.stdout_path:
            print(paint(f"--- {result.suite.longname} ({result.stdout_path}) ---", "red", enabled=color))


if __name__ == "__main__":
    sys.exit(main())
