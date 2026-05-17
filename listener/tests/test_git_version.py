"""Tests for the git version detector."""
import subprocess

import pytest

from testjam_listener import git_version


CI_ENV_VARS = (
    "GITHUB_SHA", "GITHUB_REF_NAME",
    "CI_COMMIT_SHA", "CI_COMMIT_REF_NAME",
    "GIT_COMMIT", "GIT_BRANCH",
    "BUILDKITE_COMMIT", "BUILDKITE_BRANCH",
    "CIRCLE_SHA1", "CIRCLE_BRANCH",
)


@pytest.fixture(autouse=True)
def _clear_ci_env(monkeypatch):
    for var in CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("hello")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "--no-gpg-sign", "-m", "initial"],
        cwd=tmp_path, check=True,
    )
    return tmp_path


def test_detect_uses_github_env(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "abcdef1234567890")
    monkeypatch.setenv("GITHUB_REF_NAME", "feature/x")

    version = git_version.detect()

    assert version is not None
    assert version.sha == "abcdef1234567890"
    assert version.short_sha == "abcdef1"
    assert version.branch == "feature/x"
    assert version.name == "feature/x-abcdef1"


def test_detect_uses_gitlab_env(monkeypatch):
    monkeypatch.setenv("CI_COMMIT_SHA", "deadbeef0000000000")
    monkeypatch.setenv("CI_COMMIT_REF_NAME", "master")

    version = git_version.detect()

    assert version.name == "master-deadbee"


def test_detect_strips_origin_prefix_from_jenkins(monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "1234567abcdef")
    monkeypatch.setenv("GIT_BRANCH", "origin/develop")

    version = git_version.detect()

    assert version.branch == "develop"


def test_detect_without_branch_falls_back_to_sha_only(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "abc1234deadbeef")

    version = git_version.detect()

    assert version.name == "abc1234"
    assert version.branch == "HEAD"


def test_detect_falls_back_to_local_git(repo):
    version = git_version.detect(cwd=str(repo))

    assert version is not None
    assert version.branch == "main"
    assert len(version.short_sha) == 7
    assert version.name.startswith("main-")


def test_detect_returns_none_outside_git_and_no_env(tmp_path):
    version = git_version.detect(cwd=str(tmp_path))

    assert version is None


def test_name_uses_fallback_when_no_git(tmp_path):
    assert git_version.name(cwd=str(tmp_path), fallback="unknown") == "unknown"


def test_env_overrides_local_git(monkeypatch, repo):
    monkeypatch.setenv("GITHUB_SHA", "ffffffffaaaaaaaa")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")

    version = git_version.detect(cwd=str(repo))

    assert version.sha == "ffffffffaaaaaaaa"
