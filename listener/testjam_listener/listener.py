"""Robot Framework listener that reports into Testjam in real time.

Bootstrap pulls credentials, project name and the optional version label
(``TESTJAM_VERSION``) from environment variables and reuses a single
``TestjamClient`` for the whole Robot run so the underlying HTTP connection
stays open across every event.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from testjam_client import TestjamClient
from testjam_client.errors import TestjamError, ValidationError
from testjam_listener.log import format_log_line, isoformat_timestamp
from testjam_listener.status import map_rf_status

log = logging.getLogger("testjam.listener")


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
        version_name = os.getenv("TESTJAM_VERSION")
        execution_title = os.getenv("TESTJAM_EXECUTION_TITLE")

        self.client = TestjamClient(base_url, api_key=api_key)
        if not api_key:
            if not (admin_user and admin_password):
                raise ValueError(
                    "Set TESTJAM_API_KEY or TESTJAM_USER + TESTJAM_PASS",
                )
            self.client.login(admin_user, admin_password)

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

        self.streaming_enabled = True
        # Robot always wraps the command-line target in a synthetic root suite
        # (e.g. ``robot suites/`` produces a top-level "Suites" suite). The
        # convention is to always invoke from the directory that holds the
        # real ``__init__.robot`` definitions, so we drop the synthetic root
        # to keep the Testjam hierarchy aligned with the on-disk layout.
        self._is_root_suite = True
        self._output_dir: str | None = None
        self._suite_stack: list[tuple[int, str]] = []
        self._test: _TestState | None = None
        self._step: _StepState | None = None
        self._keyword_depth = 0

    def start_suite(self, data: Any, _result: Any) -> None:
        if self._is_root_suite:
            self._is_root_suite = False
            source = getattr(data, "source", None)
            if source:
                self._output_dir = str(Path(source).parent)
            return

        parent_suite_id = self._suite_stack[-1][0] if self._suite_stack else None
        description = (getattr(data, "doc", None) or "").strip() or None
        suite = self.client.suites.find_or_create(
            self.project_id, data.name,
            parent_suite_id=parent_suite_id, description=description,
        )
        parent_path = self._suite_stack[-1][1] if self._suite_stack else ""
        suite_path = f"{parent_path}.{data.name}" if parent_path else data.name
        self._suite_stack.append((suite["id"], suite_path))

    def end_suite(self, _data: Any, _result: Any) -> None:
        if self._suite_stack:
            self._suite_stack.pop()

    def start_test(self, data: Any, _result: Any) -> None:
        current = self._suite_stack[-1] if self._suite_stack else None
        if current is None:
            self._test = None
            return
        suite_id, suite_path = current

        description = (getattr(data, "doc", None) or "").strip() or None
        tags = [str(tag) for tag in getattr(data, "tags", [])]
        external_id = f"{suite_path}.{data.name}"
        case = _find_or_create_case_by_external_id(
            self.client, suite_id, data.name,
            external_id=external_id, description=description, tags=tags,
        )
        if case is None:
            self._test = None
            return

        step_ids = _sync_steps_from_rf_test(self.client, case["id"], data)
        try:
            created = self.client.results.create(
                self.execution_id, test_case_id=case["id"],
            )
        except TestjamError:
            self._test = None
            return

        self._test = _TestState(
            result_id=created["id"], case_id=case["id"], step_ids=step_ids,
        )
        self._keyword_depth = 0
        self._safe_update_result(
            created["id"], status="running",
            executed_at=datetime.now(timezone.utc).isoformat(),
        )

    def end_test(self, _data: Any, result: Any) -> None:
        test = self._test
        if test is None:
            return
        try:
            self._safe_update_result(
                test.result_id, **_final_result_payload(result),
            )
            if not self.streaming_enabled and test.pending_step_results:
                try:
                    self.client.results.create(
                        self.execution_id,
                        test_case_id=test.case_id,
                        step_results=test.pending_step_results,
                    )
                except TestjamError:
                    pass
        finally:
            self._test = None
            self._step = None

    def start_keyword(self, _data: Any, _result: Any) -> None:
        self._keyword_depth += 1
        if self._keyword_depth != 1:
            return
        test = self._test
        if test is None or test.step_cursor >= len(test.step_ids):
            self._step = None
            return
        _step_type, step_id = test.step_ids[test.step_cursor]

        if not self.streaming_enabled:
            self._step = _StepState(step_result_id=0, step_id=step_id)
            return
        try:
            row = self.client.step_results.start(test.result_id, step_id)
            self._step = _StepState(step_result_id=row["id"], step_id=step_id)
        except TestjamError as exc:
            self._maybe_disable_streaming(exc)
            self._step = _StepState(step_result_id=0, step_id=step_id)

    def end_keyword(self, _data: Any, result: Any) -> None:
        depth = self._keyword_depth
        self._keyword_depth = max(0, depth - 1)
        if depth != 1:
            return
        test, step = self._test, self._step
        if test is None or step is None:
            return
        payload = _final_step_result_payload(result, step.log_buffer)
        try:
            if self.streaming_enabled and step.step_result_id:
                self.client.step_results.update(
                    test.result_id, step.step_result_id, **payload,
                )
            else:
                test.pending_step_results.append({"step_id": step.step_id, **payload})
        except TestjamError as exc:
            self._maybe_disable_streaming(exc)
            test.pending_step_results.append({"step_id": step.step_id, **payload})
        finally:
            self._step = None
            test.step_cursor += 1

    def log_message(self, message: Any) -> None:
        text = getattr(message, "message", "")
        if not text:
            return
        level = getattr(message, "level", "INFO")
        timestamp = getattr(message, "timestamp", None)
        test, step = self._test, self._step
        if test is None or step is None:
            return

        if not self.streaming_enabled or step.step_result_id == 0:
            step.log_buffer.append(format_log_line(level, text, timestamp))
            return
        try:
            self.client.step_results.append_log(
                test.result_id, step.step_result_id,
                level=level, message=text, ts=isoformat_timestamp(timestamp),
            )
        except TestjamError as exc:
            self._maybe_disable_streaming(exc)
            step.log_buffer.append(format_log_line(level, text, timestamp))

    def close(self) -> None:
        try:
            self.client.executions.update(
                self.execution_id,
                status="completed",
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
        except TestjamError:
            log.warning("Failed to mark execution %s completed", self.execution_id)
        self._upload_artefacts()
        self.client.close()

    def _safe_update_result(self, result_id: int, **payload: Any) -> None:
        try:
            self.client.results.update(result_id, **payload)
        except TestjamError:
            pass

    def _maybe_disable_streaming(self, exc: TestjamError) -> None:
        if 400 <= exc.status_code < 500:
            self.streaming_enabled = False
            log.info(
                "Server rejected streaming endpoint (status=%s); falling back to batch.",
                exc.status_code,
            )

    def _upload_artefacts(self) -> None:
        for filename, mime in (("log.html", "text/html"), ("output.xml", "application/xml")):
            path = _locate_artefact(self._output_dir, filename)
            if not path:
                continue
            try:
                with open(path, "rb") as file_handle:
                    self.client.executions.upload_attachment(
                        self.execution_id,
                        filename=filename, content=file_handle, mime=mime,
                    )
            except TestjamError:
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


def _final_result_payload(result: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": map_rf_status(getattr(result, "status", "")),
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
    if hasattr(result, "elapsedtime"):
        payload["duration_ms"] = int(result.elapsedtime)
    message = getattr(result, "message", None)
    if message:
        payload["comment"] = message
    return payload


def _final_step_result_payload(result: Any, log_buffer: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": map_rf_status(getattr(result, "status", ""))}
    if hasattr(result, "elapsedtime"):
        payload["duration_ms"] = int(result.elapsedtime)
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
    except (ValidationError, TestjamError):
        return None


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


def _sync_steps_from_rf_test(
    client: TestjamClient, case_id: int, data: Any,
) -> list[tuple[str, int]]:
    payload: list[dict[str, Any]] = []
    step_types: list[str] = []

    def append(action: str, step_type: str) -> None:
        payload.append({"action": action, "step_type": step_type, "order": len(payload) + 1})
        step_types.append(step_type)

    setup = getattr(data, "setup", None)
    if setup and getattr(setup, "name", None):
        append(setup.name, "setup")

    for item in getattr(data, "body", []):
        item_type = getattr(item, "type", "KEYWORD")
        action = getattr(item, "name", None) or f"[{item_type}]"
        step_type = "teardown" if item_type == "TEARDOWN" else "action"
        append(action, step_type)

    teardown = getattr(data, "teardown", None)
    if teardown and getattr(teardown, "name", None):
        append(teardown.name, "teardown")

    created = client.cases.replace_steps(case_id, payload)
    return list(zip(step_types, [row["id"] for row in created]))


def _locate_artefact(output_dir: str | None, filename: str) -> Path | None:
    candidates: list[Path] = []
    if output_dir:
        candidates.append(Path(output_dir) / "results" / filename)
        candidates.append(Path(output_dir) / filename)
    candidates.append(Path("results") / filename)
    candidates.append(Path(filename))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
