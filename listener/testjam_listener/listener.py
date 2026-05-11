"""Robot Framework listener that reports into Testjam in real time."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from testjam_listener.client import TestjamClient
from testjam_listener.log import format_log_line, isoformat_timestamp
from testjam_listener.status import map_rf_status

log = logging.getLogger("testjam.listener")


class TestjamListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self) -> None:
        base_url = os.getenv("TESTJAM_API_URL", "http://localhost:8000/api/v1")
        project_name = os.getenv("TESTJAM_PROJECT", "Robot Framework")
        api_key = os.getenv("TESTJAM_API_KEY")
        admin_user = os.getenv("TESTJAM_USER")
        admin_password = os.getenv("TESTJAM_PASS")

        self.client = TestjamClient(base_url, api_key=api_key)
        if not api_key:
            if not (admin_user and admin_password):
                raise ValueError(
                    "Set TESTJAM_API_KEY or TESTJAM_USER + TESTJAM_PASS",
                )
            self.client.login_with_password(admin_user, admin_password)

        self.project_id = self.client.find_or_create_project(project_name)
        self.execution_id = self.client.create_execution(
            self.project_id,
            title=f"Robot Run {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            type="automatic",
        )

        self.streaming_enabled = True
        self._is_root_suite = True
        self._output_dir: str | None = None
        self._suite_stack: list[int] = []
        self._test: _TestState | None = None
        self._step: _StepState | None = None

    def start_suite(self, data: Any, _result: Any) -> None:
        if self._is_root_suite:
            self._is_root_suite = False
            source = getattr(data, "source", None)
            if source:
                self._output_dir = str(Path(source).parent)
            return

        parent_suite_id = self._suite_stack[-1] if self._suite_stack else None
        description = (getattr(data, "doc", None) or "").strip() or None
        suite_id = self.client.find_or_create_suite(
            self.project_id, data.name,
            parent_suite_id=parent_suite_id, description=description,
        )
        self._suite_stack.append(suite_id)

    def end_suite(self, _data: Any, _result: Any) -> None:
        if self._suite_stack:
            self._suite_stack.pop()

    def start_test(self, data: Any, _result: Any) -> None:
        suite_id = self._suite_stack[-1] if self._suite_stack else None
        if suite_id is None:
            self._test = None
            return

        description = (getattr(data, "doc", None) or "").strip() or None
        tags = [str(tag) for tag in getattr(data, "tags", [])]
        case_id = self.client.find_or_create_case(
            suite_id, data.name, description=description, tags=tags,
        )
        if case_id is None:
            self._test = None
            return

        step_ids = _sync_steps_from_rf_test(self.client, case_id, data)
        created = self.client.create_result(self.execution_id, test_case_id=case_id)
        if not created:
            self._test = None
            return

        self._test = _TestState(
            result_id=created["id"], case_id=case_id, step_ids=step_ids,
        )
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
                self.client.create_result(
                    self.execution_id,
                    test_case_id=test.case_id,
                    step_results=test.pending_step_results,
                )
        finally:
            self._test = None
            self._step = None

    def start_keyword(self, _data: Any, _result: Any) -> None:
        test = self._test
        if test is None or test.step_cursor >= len(test.step_ids):
            self._step = None
            return
        _step_type, step_id = test.step_ids[test.step_cursor]

        if not self.streaming_enabled:
            self._step = _StepState(step_result_id=0, step_id=step_id)
            return
        try:
            row = self.client.start_step_result(test.result_id, step_id)
            self._step = _StepState(step_result_id=row["id"], step_id=step_id)
        except requests.HTTPError as exc:
            self._maybe_disable_streaming(exc)
            self._step = _StepState(step_result_id=0, step_id=step_id)
        except requests.RequestException:
            self._step = None

    def end_keyword(self, _data: Any, result: Any) -> None:
        test, step = self._test, self._step
        if test is None or step is None:
            return
        payload = _final_step_result_payload(result, step.log_buffer)
        try:
            if self.streaming_enabled and step.step_result_id:
                response = self.client.update_step_result(
                    test.result_id, step.step_result_id, **payload,
                )
                response.raise_for_status()
            else:
                test.pending_step_results.append({"step_id": step.step_id, **payload})
        except requests.HTTPError as exc:
            self._maybe_disable_streaming(exc)
            test.pending_step_results.append({"step_id": step.step_id, **payload})
        except requests.RequestException:
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
            response = self.client.append_step_result_log(
                test.result_id, step.step_result_id,
                level=level, message=text,
                timestamp_iso=isoformat_timestamp(timestamp),
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            self._maybe_disable_streaming(exc)
            step.log_buffer.append(format_log_line(level, text, timestamp))
        except requests.RequestException:
            step.log_buffer.append(format_log_line(level, text, timestamp))

    def close(self) -> None:
        try:
            self.client.update_execution(
                self.execution_id,
                status="completed",
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
        except requests.RequestException:
            log.warning("Failed to mark execution %s completed", self.execution_id)
        self._upload_artefacts()

    def _safe_update_result(self, result_id: int, **payload: Any) -> None:
        try:
            self.client.update_result(result_id, **payload)
        except requests.RequestException:
            pass

    def _maybe_disable_streaming(self, exc: requests.HTTPError) -> None:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code is not None and 400 <= status_code < 500:
            self.streaming_enabled = False
            log.info(
                "Server rejected streaming endpoint (status=%s); falling back to batch.",
                status_code,
            )

    def _upload_artefacts(self) -> None:
        for filename, mime in (("log.html", "text/html"), ("output.xml", "application/xml")):
            path = _locate_artefact(self._output_dir, filename)
            if not path:
                continue
            with open(path, "rb") as file_handle:
                self.client.upload_execution_attachment(
                    self.execution_id,
                    filename=filename, file_handle=file_handle, mime=mime,
                )


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


def _sync_steps_from_rf_test(
    client: TestjamClient, case_id: int, data: Any,
) -> list[tuple[str, int]]:
    client.delete_all_case_steps(case_id)
    step_ids: list[tuple[str, int]] = []
    order = 1

    setup = getattr(data, "setup", None)
    if setup and getattr(setup, "name", None):
        step_id = client.create_step(case_id, action=setup.name, order=order, step_type="setup")
        if step_id is not None:
            step_ids.append(("setup", step_id))
        order += 1

    for item in getattr(data, "body", []):
        item_type = getattr(item, "type", "KEYWORD")
        action = getattr(item, "name", None) or f"[{item_type}]"
        step_type = "teardown" if item_type == "TEARDOWN" else "action"
        step_id = client.create_step(case_id, action=action, order=order, step_type=step_type)
        if step_id is not None:
            step_ids.append((step_type, step_id))
        order += 1

    teardown = getattr(data, "teardown", None)
    if teardown and getattr(teardown, "name", None):
        step_id = client.create_step(case_id, action=teardown.name, order=order, step_type="teardown")
        if step_id is not None:
            step_ids.append(("teardown", step_id))

    return step_ids


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
