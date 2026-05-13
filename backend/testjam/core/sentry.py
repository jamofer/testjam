import os
import re
import subprocess
from importlib.metadata import PackageNotFoundError, version
from typing import Any
from urllib.parse import parse_qsl, urlencode

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from testjam.core.logging import current_request_id

SCRUBBED_HEADERS = {"authorization", "cookie", "x-api-key"}
SCRUBBED_BODY_KEYS = {
    "password", "new_password", "current_password", "token", "access_token",
    "refresh_token", "api_key", "secret",
}
URL_QUERY_PATTERN = re.compile(r"^([^?]*)\?(.*)$")


def configure_sentry() -> None:
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        release=_release(),
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=_float_env("SENTRY_TRACES_SAMPLE_RATE", 0.0),
        profiles_sample_rate=_float_env("SENTRY_PROFILES_SAMPLE_RATE", 0.0),
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        before_send=_before_send,
    )


def _before_send(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any]:
    request_id = current_request_id()
    if request_id:
        event.setdefault("tags", {})["request_id"] = request_id
    _scrub_request(event.get("request"))
    return event


def _scrub_request(request: dict[str, Any] | None) -> None:
    if not request:
        return
    headers = request.get("headers")
    if isinstance(headers, dict):
        for key in list(headers):
            if key.lower() in SCRUBBED_HEADERS:
                headers[key] = "[scrubbed]"
    data = request.get("data")
    if isinstance(data, dict):
        for key in list(data):
            if key.lower() in SCRUBBED_BODY_KEYS:
                data[key] = "[scrubbed]"
    if isinstance(request.get("query_string"), str):
        request["query_string"] = _scrub_query_string(request["query_string"])
    if isinstance(request.get("url"), str):
        request["url"] = _scrub_url(request["url"])


def _scrub_query_string(query: str) -> str:
    pairs = parse_qsl(query, keep_blank_values=True)
    if not pairs:
        return query
    cleaned = [
        (key, "[scrubbed]" if key.lower() in SCRUBBED_BODY_KEYS else value)
        for key, value in pairs
    ]
    return urlencode(cleaned)


def _scrub_url(url: str) -> str:
    match = URL_QUERY_PATTERN.match(url)
    if not match:
        return url
    base, query = match.group(1), match.group(2)
    return f"{base}?{_scrub_query_string(query)}"


def _release() -> str:
    package_version = _package_version()
    sha = _git_sha()
    if sha:
        return f"testjam-api@{package_version}+{sha}"
    return f"testjam-api@{package_version}"


def _package_version() -> str:
    try:
        return version("testjam-api")
    except PackageNotFoundError:
        return "unknown"


def _git_sha() -> str | None:
    sha = os.environ.get("GIT_SHA", "").strip()
    if sha:
        return sha[:12]
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return output.decode().strip() or None
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default
