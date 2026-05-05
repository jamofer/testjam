"""
Robot Framework listener that reports E2E results back into Testjam itself.

  - finds or creates the configured project (default: "Testjam E2E")
  - finds or creates one Testjam suite per .robot file suite (idempotent by name)
  - finds or creates one Testjam case per test (idempotent by name within suite)
  - syncs RF metadata every run: description, tags, steps from body
  - reports pass/fail/skip + duration + step results for each test
  - uploads log.html and output.xml as execution attachments when the run ends

Configuration via environment variables (all optional):
  TESTJAM_BASE_URL      — e.g. http://localhost:8000/api/v1
  TESTJAM_ADMIN_USER    — default: admin
  TESTJAM_ADMIN_PASS    — default: admin123
  TESTJAM_E2E_PROJECT   — project name, default: Testjam E2E
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


class TestjamE2EListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self) -> None:
        base_url = os.getenv("TESTJAM_BASE_URL", "http://localhost:8000/api/v1")
        user = os.getenv("TESTJAM_ADMIN_USER", "admin")
        password = os.getenv("TESTJAM_ADMIN_PASS", "admin123")
        project_name = os.getenv("TESTJAM_E2E_PROJECT", "Testjam E2E")

        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._suite_stack: list[int] = []
        # longname → {"result_id": int, "case_id": int, "step_ids": list[tuple[str, int]]}
        self._result_map: dict[str, dict] = {}
        self._is_root_suite = True
        self._output_dir: str | None = None

        self._authenticate(user, password)
        self._project_id = self._find_or_create_project(project_name)
        self._execution_id = self._create_execution()

    # ── Bootstrap ─────────────────────────────────────────────────────────────

    def _authenticate(self, user: str, password: str) -> None:
        resp = self._session.post(
            f"{self._base}/auth/login",
            data={"username": user, "password": password},
        )
        resp.raise_for_status()
        self._session.headers.update({"Authorization": f"Bearer {resp.json()['access_token']}"})

    def _find_or_create_project(self, name: str) -> int:
        resp = self._session.get(f"{self._base}/projects")
        resp.raise_for_status()
        for p in resp.json():
            if p["name"] == name:
                return p["id"]
        resp = self._session.post(f"{self._base}/projects", json={"name": name})
        resp.raise_for_status()
        return resp.json()["id"]

    def _create_execution(self) -> int:
        title = f"E2E Run {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        resp = self._session.post(
            f"{self._base}/projects/{self._project_id}/executions",
            json={"title": title, "type": "automatic"},
        )
        resp.raise_for_status()
        return resp.json()["id"]

    # ── Suite helpers ─────────────────────────────────────────────────────────

    def _find_or_create_suite(self, name: str, parent_suite_id: int | None, description: str) -> int | None:
        params: dict = {"name": name}
        if parent_suite_id is not None:
            params["parent_suite_id"] = parent_suite_id
        resp = self._session.get(f"{self._base}/projects/{self._project_id}/suites", params=params)
        if resp.ok and resp.json():
            suite_id = resp.json()[0]["id"]
            if description:
                self._session.put(f"{self._base}/suites/{suite_id}", json={"description": description})
            return suite_id

        body: dict = {"name": name}
        if parent_suite_id is not None:
            body["parent_suite_id"] = parent_suite_id
        if description:
            body["description"] = description
        resp = self._session.post(f"{self._base}/projects/{self._project_id}/suites", json=body)
        return resp.json()["id"] if resp.ok else None

    # ── Case helpers ──────────────────────────────────────────────────────────

    def _find_or_create_case(self, suite_id: int, name: str, description: str, tags: list[str]) -> int | None:
        resp = self._session.get(f"{self._base}/suites/{suite_id}/cases", params={"name": name})
        if resp.ok and resp.json():
            case_id = resp.json()[0]["id"]
            update: dict = {"tags": tags}
            if description:
                update["description"] = description
            self._session.put(f"{self._base}/cases/{case_id}", json=update)
            return case_id

        body: dict = {"name": name, "suite_id": suite_id, "tags": tags}
        if description:
            body["description"] = description
        resp = self._session.post(f"{self._base}/suites/{suite_id}/cases", json=body)
        return resp.json()["id"] if resp.ok else None

    # ── Step sync ─────────────────────────────────────────────────────────────

    def _sync_steps(self, case_id: int, data: Any) -> list[tuple[str, int]]:
        """Delete all steps and recreate from RF body. Returns list of (step_type, step_id) in order."""
        self._session.delete(f"{self._base}/cases/{case_id}/steps")
        step_ids: list[tuple[str, int]] = []
        order = 1

        setup = getattr(data, "setup", None)
        if setup and getattr(setup, "name", None):
            resp = self._session.post(
                f"{self._base}/cases/{case_id}/steps",
                json={"action": setup.name, "step_type": "setup", "order": order},
            )
            if resp.ok:
                step_ids.append(("setup", resp.json()["id"]))
            order += 1

        for item in getattr(data, "body", []):
            item_type = getattr(item, "type", "KEYWORD")
            action = getattr(item, "name", None) or f"[{item_type}]"
            step_type = "teardown" if item_type == "TEARDOWN" else "action"
            resp = self._session.post(
                f"{self._base}/cases/{case_id}/steps",
                json={"action": action, "step_type": step_type, "order": order},
            )
            if resp.ok:
                step_ids.append((step_type, resp.json()["id"]))
            order += 1

        teardown = getattr(data, "teardown", None)
        if teardown and getattr(teardown, "name", None):
            resp = self._session.post(
                f"{self._base}/cases/{case_id}/steps",
                json={"action": teardown.name, "step_type": "teardown", "order": order},
            )
            if resp.ok:
                step_ids.append(("teardown", resp.json()["id"]))

        return step_ids

    # ── Log extraction ────────────────────────────────────────────────────────

    def _collect_log(self, item: Any) -> str | None:
        # In RF v7 the `messages` property is just body filtered to MESSAGE type —
        # iterating both would duplicate every line. Use body exclusively.
        lines: list[str] = []
        for child in getattr(item, "body", []):
            if getattr(child, "type", "") == "MESSAGE":
                level = getattr(child, "level", "INFO")
                text = getattr(child, "message", "").strip()
                if not text:
                    continue
                ts = getattr(child, "timestamp", None)
                if ts:
                    if hasattr(ts, "strftime"):
                        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S.") + f"{ts.microsecond // 1000:03d}"
                    else:
                        ts_str = str(ts)
                    lines.append(f"{ts_str} [{level}] {text}")
                else:
                    lines.append(f"[{level}] {text}")
        return "\n".join(lines) or None

    # ── Listener hooks ────────────────────────────────────────────────────────

    def start_suite(self, data: Any, result: Any) -> None:
        if self._is_root_suite:
            self._is_root_suite = False
            source = getattr(data, "source", None)
            if source:
                self._output_dir = str(Path(source).parent)
            return

        parent_id = self._suite_stack[-1] if self._suite_stack else None
        doc = (getattr(data, "doc", None) or "").strip()
        suite_id = self._find_or_create_suite(data.name, parent_id, doc)
        self._suite_stack.append(suite_id)

    def end_suite(self, data: Any, result: Any) -> None:
        if self._suite_stack:
            self._suite_stack.pop()

    def start_test(self, data: Any, result: Any) -> None:
        suite_id = self._suite_stack[-1] if self._suite_stack else None
        if suite_id is None:
            return

        doc = (getattr(data, "doc", None) or "").strip()
        tags = [str(t) for t in getattr(data, "tags", [])]

        case_id = self._find_or_create_case(suite_id, data.name, doc, tags)
        if case_id is None:
            return

        step_ids = self._sync_steps(case_id, data)

        resp = self._session.post(
            f"{self._base}/executions/{self._execution_id}/results",
            json={"test_case_id": case_id},
        )
        if resp.ok:
            self._result_map[data.longname] = {
                "result_id": resp.json()["id"],
                "case_id": case_id,
                "step_ids": step_ids,
            }

    def end_test(self, data: Any, result: Any) -> None:
        info = self._result_map.get(data.longname)
        if not info:
            return

        result_id = info["result_id"]
        step_ids = info["step_ids"]  # list of (step_type, step_id)

        status_map = {"PASS": "passed", "FAIL": "failed", "SKIP": "blocked"}

        payload: dict = {
            "status": status_map.get(result.status, "not_run"),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        if hasattr(result, "elapsedtime"):
            payload["duration_ms"] = int(result.elapsedtime)
        if result.message:
            payload["comment"] = result.message

        self._session.put(f"{self._base}/results/{result_id}", json=payload)

        if not step_ids:
            return

        # Match result body items to step_ids by position
        step_results: list[dict] = []
        idx = 0

        def add_sr(kw_result: Any, step_type: str) -> None:
            nonlocal idx
            if idx >= len(step_ids):
                return
            st, sid = step_ids[idx]
            if st != step_type:
                return
            step_results.append({
                "step_id": sid,
                "status": status_map.get(getattr(kw_result, "status", ""), "not_run"),
                "log_output": self._collect_log(kw_result),
            })
            idx += 1

        setup_result = getattr(result, "setup", None)
        if setup_result:
            add_sr(setup_result, "setup")

        for kw_result in getattr(result, "body", []):
            item_type = getattr(kw_result, "type", "KEYWORD")
            st = "teardown" if item_type == "TEARDOWN" else "action"
            add_sr(kw_result, st)

        teardown_result = getattr(result, "teardown", None)
        if teardown_result:
            add_sr(teardown_result, "teardown")

        if step_results:
            self._session.post(
                f"{self._base}/executions/{self._execution_id}/results",
                json={"test_case_id": info["case_id"], "step_results": step_results},
            )

    def close(self) -> None:
        self._session.put(
            f"{self._base}/executions/{self._execution_id}",
            json={"status": "completed", "finished_at": datetime.now(timezone.utc).isoformat()},
        )
        self._upload_artifacts()

    def _upload_artifacts(self) -> None:
        artifacts = [
            ("log.html", "text/html"),
            ("output.xml", "application/xml"),
        ]
        for filename, mime in artifacts:
            candidates = [
                self._output_dir and Path(self._output_dir) / "results" / filename,
                self._output_dir and Path(self._output_dir) / filename,
                Path("results") / filename,
                Path(filename),
            ]
            for path in candidates:
                if path and Path(path).exists():
                    with open(path, "rb") as fh:
                        self._session.post(
                            f"{self._base}/executions/{self._execution_id}/attachments",
                            files={"file": (filename, fh, mime)},
                        )
                    break
