"""Turns copied Robot events into Testjam suites, cases, results and logs.

Runs on the outbox worker: every method is called in the order Robot fired the
events, one at a time, so the suite stack and the current test/step state need
no locking.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx

from testjam_client import TestjamClient, statuses
from testjam_client.errors import Conflict, TestjamError
from testjam_client.listener.events import LogEvent, OutcomeEvent, SuiteEvent, TestEvent
from testjam_client.listener.log import format_log_line, isoformat_timestamp
from testjam_client.listener.status import map_rf_status

log = logging.getLogger("testjam.listener")

API_ERRORS = (TestjamError, httpx.TransportError)
# The API refuses text/html uploads; log.html is served as a download either way.
ARTEFACT_TYPES = {"log.html": "application/octet-stream", "output.xml": "application/xml"}
ABORT_MESSAGES = ("Execution terminated by signal", "Test execution stopped due to a fatal error")
CF_TAG_PREFIX = "cf:"


class Reporter:
    def __init__(self, client: TestjamClient, *, project_id: int, execution_id: int) -> None:
        self.client = client
        self.project_id = project_id
        self.execution_id = execution_id
        self.streaming_enabled = True
        self.current_test: _TestState | None = None
        self.current_step: _StepState | None = None
        self._execution_custom_fields: dict[str, Any] = {}
        # ``robot suites/`` wraps the run in a top-level "Suites" directory
        # suite; dropping it keeps the Testjam hierarchy aligned with the
        # on-disk layout. ``robot file.robot`` has no such wrapper: the root
        # suite is the file itself and holds the tests.
        self._is_root_suite = True
        self._is_aborted = False
        self._artefact_paths: dict[str, str] = {}
        self._suite_stack: list[tuple[int | None, str]] = []
        self._body_depth = 0

    def start_suite(self, suite: SuiteEvent) -> None:
        if self._is_root_suite:
            self._is_root_suite = False
            if not _is_file_suite(suite.source):
                return

        parent_suite_id, parent_path = self._suite_stack[-1] if self._suite_stack else (None, "")
        suite_path = f"{parent_path}.{suite.name}" if parent_path else suite.name
        suite_id = None
        if parent_suite_id is not None or not self._suite_stack:
            suite_id = self._find_or_create_suite(suite, parent_suite_id)
        self._suite_stack.append((suite_id, suite_path))

    def end_suite(self) -> None:
        if self._suite_stack:
            self._suite_stack.pop()

    def start_test(self, test: TestEvent) -> None:
        self.current_test = None
        self._body_depth = 0
        suite_id, suite_path = self._suite_stack[-1] if self._suite_stack else (None, "")
        if suite_id is None:
            return
        try:
            self.current_test = self._begin_test(test, suite_id, suite_path)
        except API_ERRORS as exc:
            log.warning("Skipping test %s: %s", test.name, exc)

    def end_test(self, outcome: OutcomeEvent) -> None:
        if outcome.message.startswith(ABORT_MESSAGES):
            self._is_aborted = True
        test = self.current_test
        if test is None:
            return
        try:
            self._safe_update_result(test.result_id, **_final_result_payload(outcome))
            if not self.streaming_enabled and test.pending_step_results:
                self._create_batched_result(test)
        finally:
            self.current_test = None
            self.current_step = None

    def start_body_item(self) -> None:
        """Track top-level items, each of which maps to one case step.

        ``start_keyword`` would skip FOR and IF and fire for the keywords inside
        them instead, shifting every later step.
        """
        self._body_depth += 1
        if self._body_depth != 1:
            return
        test = self.current_test
        if test is None or test.step_cursor >= len(test.step_ids):
            self.current_step = None
            return
        _step_type, step_id = test.step_ids[test.step_cursor]
        self.current_step = self._start_step(test, step_id)

    def end_body_item(self, outcome: OutcomeEvent) -> None:
        depth = self._body_depth
        self._body_depth = max(0, depth - 1)
        if depth != 1:
            return
        test, step = self.current_test, self.current_step
        if test is None or step is None:
            return
        payload = _final_step_result_payload(outcome, step.log_buffer)
        try:
            if self.streaming_enabled and step.step_result_id:
                self.client.step_results.update(test.result_id, step.step_result_id, **payload)
            else:
                test.pending_step_results.append({"step_id": step.step_id, **payload})
        except API_ERRORS as exc:
            self._maybe_disable_streaming(exc)
            test.pending_step_results.append({"step_id": step.step_id, **payload})
        finally:
            self.current_step = None
            test.step_cursor += 1

    def log_message(self, message: LogEvent) -> None:
        test, step = self.current_test, self.current_step
        if test is None or step is None:
            return
        line = format_log_line(message.level, message.message, message.timestamp)
        if not self.streaming_enabled or step.step_result_id == 0:
            step.log_buffer.append(line)
            return
        try:
            self.client.step_results.append_log(
                test.result_id, step.step_result_id,
                level=message.level, message=message.message,
                ts=isoformat_timestamp(message.timestamp),
            )
        except API_ERRORS as exc:
            self._maybe_disable_streaming(exc)
            step.log_buffer.append(line)

    def record_artefact(self, filename: str, path: str) -> None:
        self._artefact_paths[filename] = path

    def finish(self, finished_at: str) -> None:
        update_payload: dict[str, Any] = {
            "status": statuses.ABORTED if self._is_aborted else statuses.COMPLETED,
            "finished_at": finished_at,
        }
        if self._execution_custom_fields:
            update_payload["custom_fields"] = self._execution_custom_fields
        try:
            self.client.executions.update(self.execution_id, **update_payload)
        except API_ERRORS:
            log.warning("Failed to close execution %s", self.execution_id)
        self._upload_artefacts()

    def _begin_test(self, test: TestEvent, suite_id: int, suite_path: str) -> _TestState | None:
        tags = list(test.tags)
        self._execution_custom_fields.update(_parse_cf_tags(tags))
        case = _find_or_create_case_by_external_id(
            self.client, suite_id, test.name,
            external_id=f"{suite_path}.{test.name}",
            description=test.description, tags=tags,
        )
        if case is None:
            return None

        step_ids = _sync_steps(self.client, case["id"], test)
        try:
            created = self.client.results.create(self.execution_id, test_case_id=case["id"])
        except API_ERRORS:
            return None

        self._safe_update_result(created["id"], status="running", executed_at=test.started_at)
        return _TestState(result_id=created["id"], case_id=case["id"], step_ids=step_ids)

    def _start_step(self, test: _TestState, step_id: int) -> _StepState:
        if not self.streaming_enabled:
            return _StepState(step_result_id=0, step_id=step_id)
        try:
            row = self.client.step_results.start(test.result_id, step_id)
        except API_ERRORS as exc:
            self._maybe_disable_streaming(exc)
            return _StepState(step_result_id=0, step_id=step_id)
        return _StepState(step_result_id=row["id"], step_id=step_id)

    def _create_batched_result(self, test: _TestState) -> None:
        try:
            self.client.results.create(
                self.execution_id,
                test_case_id=test.case_id,
                step_results=test.pending_step_results,
            )
        except API_ERRORS:
            pass

    def _find_or_create_suite(self, suite: SuiteEvent, parent_suite_id: int | None) -> int | None:
        try:
            created = self.client.suites.find_or_create(
                self.project_id, suite.name,
                parent_suite_id=parent_suite_id, description=suite.description,
            )
        except API_ERRORS as exc:
            log.warning("Skipping suite %s: %s", suite.name, exc)
            return None
        return created["id"]

    def _safe_update_result(self, result_id: int, **payload: Any) -> None:
        try:
            self.client.results.update(result_id, **payload)
        except API_ERRORS:
            pass

    def _maybe_disable_streaming(self, exc: Exception) -> None:
        if isinstance(exc, httpx.TransportError) or 400 <= exc.status_code < 500:
            self.streaming_enabled = False
            log.info("Streaming unavailable (%s); falling back to batch.", exc)

    def _upload_artefacts(self) -> None:
        for filename, mime in ARTEFACT_TYPES.items():
            path = self._artefact_paths.get(filename)
            if path is None:
                continue
            try:
                self.client.executions.upload_attachment(
                    self.execution_id,
                    filename=filename, content=Path(path).read_bytes(), mime=mime,
                )
            except (*API_ERRORS, OSError):
                log.warning("Failed to upload %s for execution %s", filename, self.execution_id)


class _TestState:
    __slots__ = ("result_id", "case_id", "step_ids", "step_cursor", "pending_step_results")

    def __init__(self, *, result_id: int, case_id: int, step_ids: list[tuple[str, int]]) -> None:
        self.result_id = result_id
        self.case_id = case_id
        self.step_ids = step_ids
        self.step_cursor = 0
        self.pending_step_results: list[dict[str, Any]] = []


class _StepState:
    __slots__ = ("step_result_id", "step_id", "log_buffer")

    def __init__(self, *, step_result_id: int, step_id: int) -> None:
        self.step_result_id = step_result_id
        self.step_id = step_id
        self.log_buffer: list[str] = []


def _final_result_payload(outcome: OutcomeEvent) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": map_rf_status(outcome.status),
        "executed_at": outcome.finished_at,
    }
    if outcome.duration_ms is not None:
        payload["duration_ms"] = outcome.duration_ms
    if outcome.message:
        payload["comment"] = outcome.message
    return payload


def _final_step_result_payload(outcome: OutcomeEvent, log_buffer: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": map_rf_status(outcome.status)}
    if outcome.duration_ms is not None:
        payload["duration_ms"] = outcome.duration_ms
    if log_buffer:
        payload["log_output"] = "\n".join(log_buffer)
    return payload


def _find_or_create_case_by_external_id(
    client: TestjamClient,
    suite_id: int,
    name: str,
    *,
    external_id: str,
    description: str | None = None,
    tags: list[str] | None = None,
) -> dict | None:
    """Match by external_id (Robot suite path + test name) for stable identity.

    Falls back to name lookup for legacy cases that pre-date the external_id
    convention. When a legacy match is found, the external_id is stamped on
    that row so future runs hit the fast path.
    """
    by_external = client.cases.list(suite_id, external_id=external_id, include_archived=True)
    if by_external:
        return _refresh_case(client, by_external[0], name, description, tags)

    by_name = client.cases.list(suite_id, name=name, include_archived=True)
    legacy = next((c for c in by_name if not c.get("external_id")), None)
    if legacy is not None:
        client.cases.update(legacy["id"], external_id=external_id)
        legacy["external_id"] = external_id
        return _refresh_case(client, legacy, name, description, tags)

    try:
        return client.cases.create(
            suite_id, name,
            external_id=external_id,
            description=description, tags=tags,
        )
    except Conflict:
        return _find_case_created_concurrently(client, suite_id, name, external_id)


def _find_case_created_concurrently(
    client: TestjamClient, suite_id: int, name: str, external_id: str,
) -> dict | None:
    """A parallel worker won the race, or the name is taken under another identity."""
    matches = (
        client.cases.list(suite_id, external_id=external_id, include_archived=True)
        or client.cases.list(suite_id, name=name, include_archived=True)
    )
    return matches[0] if matches else None


def _refresh_case(
    client: TestjamClient,
    case: dict,
    name: str,
    description: str | None,
    tags: list[str] | None,
) -> dict:
    if case.get("archived_at") is not None:
        client.cases.unarchive(case["id"])
    update_payload: dict[str, Any] = {}
    if case.get("name") != name:
        update_payload["name"] = name
    if description is not None and case.get("description") != description:
        update_payload["description"] = description
    if tags is not None and (case.get("tags") or []) != tags:
        update_payload["tags"] = tags
    if update_payload:
        client.cases.update(case["id"], **update_payload)
    return case


def _sync_steps(client: TestjamClient, case_id: int, test: TestEvent) -> list[tuple[str, int]]:
    payload = [
        {"action": step.action, "step_type": step.step_type, "order": order}
        for order, step in enumerate(test.steps, start=1)
    ]
    step_types = [step.step_type for step in test.steps]

    existing = client.cases.list_steps(case_id)
    if _steps_match(existing, payload):
        return list(zip(step_types, [row["id"] for row in existing]))

    created = client.cases.replace_steps(case_id, payload)
    return list(zip(step_types, [row["id"] for row in created]))


def _steps_match(existing: list[dict[str, Any]], payload: list[dict[str, Any]]) -> bool:
    """Return True when the backend already has the exact same step sequence.

    Compares action / step_type / order so a no-op listener replay does not
    rewrite the steps and create a redundant CaseRevision.
    """
    if len(existing) != len(payload):
        return False
    for current, incoming in zip(
        sorted(existing, key=lambda row: row.get("order", 0)), payload,
    ):
        if current.get("action") != incoming["action"]:
            return False
        if current.get("step_type", "action") != incoming.get("step_type", "action"):
            return False
        if current.get("order") != incoming["order"]:
            return False
    return True


def _parse_cf_tags(tags: list[str]) -> dict[str, Any]:
    """Convert ``cf:key=value`` Robot tags to a custom_fields dict.

    Comma-separated values become lists for multi_select fields.
    Tags missing the ``=`` or with empty key/value are ignored.
    """
    result: dict[str, Any] = {}
    for tag in tags:
        if not tag.startswith(CF_TAG_PREFIX):
            continue
        body = tag[len(CF_TAG_PREFIX):]
        if "=" not in body:
            continue
        key, _, raw = body.partition("=")
        key = key.strip()
        raw = raw.strip()
        if not key or not raw:
            continue
        if "," in raw:
            items = [item.strip() for item in raw.split(",") if item.strip()]
            result[key] = items
        else:
            result[key] = raw
    return result


def _is_file_suite(source: str | None) -> bool:
    return bool(source) and Path(source).is_file()
