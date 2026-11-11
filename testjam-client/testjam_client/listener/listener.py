"""Robot Framework listener that reports into Testjam in real time.

Bootstrap pulls credentials, project name and the optional version label
(``TESTJAM_VERSION``) from environment variables and reuses a single
``TestjamClient`` for the whole Robot run so the underlying HTTP connection
stays open across every event.

Bootstrap runs on Robot's thread so bad credentials fail the run up front.
After that each event is copied and queued, and a background worker reports
it, so a slow or unreachable server never holds up the tests. ``close`` waits
for the queue to drain before Robot exits.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from testjam_client import TestjamClient
from testjam_client.listener.circuit_breaker import NetworkCircuitBreaker
from testjam_client.listener.events import (
    LogEvent,
    OutcomeEvent,
    SuiteEvent,
    TestEvent,
    now_isoformat,
)
from testjam_client.listener.outbox import Outbox
from testjam_client.listener.reporter import Reporter
from testjam_client.listener.session_renewal import SessionRenewal

MAX_CONSECUTIVE_NETWORK_FAILURES = 3
NETWORK_RETRY_COOLDOWN_SECONDS = 60.0


class TestjamListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self) -> None:
        # Silence httpx INFO request logs — Robot captures them and the
        # listener would forward each back to /log, creating a recursive
        # log-of-log loop that empoisons the test logs and eventually
        # blows the recursion stack.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        base_url = os.getenv("TESTJAM_API_URL", "http://localhost:8000/api/v1")
        project_name = os.getenv("TESTJAM_PROJECT", "Robot Framework")
        api_key = os.getenv("TESTJAM_API_KEY")
        admin_user = os.getenv("TESTJAM_USER")
        admin_password = os.getenv("TESTJAM_PASS")
        version_name = os.getenv("TESTJAM_VERSION") or None
        execution_title = os.getenv("TESTJAM_EXECUTION_TITLE")

        self.client = TestjamClient(base_url, api_key=api_key)
        self.client.wrap_http(
            lambda http: NetworkCircuitBreaker(
                http,
                max_failures=MAX_CONSECUTIVE_NETWORK_FAILURES,
                cooldown_seconds=NETWORK_RETRY_COOLDOWN_SECONDS,
            ),
        )
        if not api_key:
            if not (admin_user and admin_password):
                raise ValueError(
                    "Set TESTJAM_API_KEY or TESTJAM_USER + TESTJAM_PASS",
                )
            self.client.login(admin_user, admin_password)
            self.client.wrap_http(
                lambda http: SessionRenewal(
                    http, renew=lambda: self.client.login(admin_user, admin_password),
                ),
            )

        project = self.client.projects.find_or_create(project_name)
        self.project_id = project["id"]

        version_id = None
        if version_name:
            version = self.client.versions.find_or_create(self.project_id, version_name)
            version_id = version["id"]

        title = execution_title or f"Robot Run {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        execution = self.client.executions.create(
            self.project_id,
            title=title,
            type="automatic",
            version_id=version_id,
        )
        self.execution_id = execution["id"]

        self.reporter = Reporter(
            self.client, project_id=self.project_id, execution_id=self.execution_id,
        )
        self._outbox = Outbox()

    def start_suite(self, data: Any, _result: Any) -> None:
        self._outbox.submit(self.reporter.start_suite, SuiteEvent.from_robot(data))

    def end_suite(self, _data: Any, _result: Any) -> None:
        self._outbox.submit(self.reporter.end_suite)

    def start_test(self, data: Any, _result: Any) -> None:
        self._outbox.submit(self.reporter.start_test, TestEvent.from_robot(data))

    def end_test(self, _data: Any, result: Any) -> None:
        self._outbox.submit(self.reporter.end_test, OutcomeEvent.from_robot(result))

    def start_body_item(self, _data: Any, _result: Any) -> None:
        self._outbox.submit(self.reporter.start_body_item)

    def end_body_item(self, _data: Any, result: Any) -> None:
        self._outbox.submit(self.reporter.end_body_item, OutcomeEvent.from_robot(result))

    def log_message(self, message: Any) -> None:
        if getattr(message, "message", ""):
            self._outbox.submit(self.reporter.log_message, LogEvent.from_robot(message))

    def output_file(self, path: str) -> None:
        self._outbox.submit(self.reporter.record_artefact, "output.xml", path)

    def log_file(self, path: str) -> None:
        self._outbox.submit(self.reporter.record_artefact, "log.html", path)

    def flush(self) -> None:
        """Block until every event received so far has been reported."""
        self._outbox.flush()

    def close(self) -> None:
        self._outbox.submit(self.reporter.finish, now_isoformat())
        try:
            self._outbox.close()
        finally:
            self.client.close()
