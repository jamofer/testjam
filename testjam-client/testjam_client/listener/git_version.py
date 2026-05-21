"""Derive a stable Testjam version label from the current git commit.

Priority:

1. **CI environment variables.** GitHub Actions, GitLab CI, Jenkins and
   generic ``GIT_COMMIT`` / ``GIT_BRANCH`` exports are recognised so the
   orchestrator does not have to shell out inside a container that lacks git.
2. **Local ``git`` invocation.** ``git rev-parse HEAD`` +
   ``git symbolic-ref --short HEAD`` (detached HEAD falls back to ``HEAD``).

The default ``name`` format is ``{branch}-{short_sha}`` (e.g.
``master-abc1234``) so the same commit on the same branch always maps to the
same Testjam Version, while different branches stay distinct.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


SHORT_SHA_LEN = 7
DEFAULT_BRANCH = "HEAD"


@dataclass(frozen=True)
class GitVersion:
    branch: str
    sha: str
    name: str
    short_sha: str


def detect(cwd: str | None = None) -> GitVersion | None:
    """Resolve git metadata for the current commit or return ``None``."""
    branch, sha = _from_env() or _from_git(cwd) or (None, None)
    if not sha:
        return None
    short = sha[:SHORT_SHA_LEN]
    return GitVersion(
        branch=branch or DEFAULT_BRANCH,
        sha=sha,
        short_sha=short,
        name=_format_name(branch, short),
    )


def name(cwd: str | None = None, *, fallback: str | None = None) -> str | None:
    version = detect(cwd)
    if version is not None:
        return version.name
    return fallback


def _from_env() -> tuple[str | None, str | None] | None:
    sha = (
        os.getenv("GITHUB_SHA")
        or os.getenv("CI_COMMIT_SHA")
        or os.getenv("GIT_COMMIT")
        or os.getenv("BUILDKITE_COMMIT")
        or os.getenv("CIRCLE_SHA1")
    )
    if not sha:
        return None
    branch = (
        os.getenv("GITHUB_REF_NAME")
        or os.getenv("CI_COMMIT_REF_NAME")
        or _strip_origin(os.getenv("GIT_BRANCH"))
        or os.getenv("BUILDKITE_BRANCH")
        or os.getenv("CIRCLE_BRANCH")
    )
    return branch, sha


def _from_git(cwd: str | None) -> tuple[str | None, str | None] | None:
    sha = _git(["rev-parse", "HEAD"], cwd)
    if not sha:
        return None
    branch = _git(["symbolic-ref", "--short", "HEAD"], cwd)
    return branch, sha


def _git(args: list[str], cwd: str | None) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def _strip_origin(value: str | None) -> str | None:
    if not value:
        return value
    return value.removeprefix("origin/")


def _format_name(branch: str | None, short_sha: str) -> str:
    if not branch or branch == DEFAULT_BRANCH:
        return short_sha
    return f"{branch}-{short_sha}"
