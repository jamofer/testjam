"""
Robot Framework listener v3 for real-time reporting to Testjam.

Usage in robot command:
    robot --listener testjam_listener.TestjamListener \
          --variable TESTJAM_URL:http://localhost:8000/api/v1 \
          --variable TESTJAM_API_KEY:your-api-key \
          --variable TESTJAM_EXECUTION_ID:42 \
          tests/

Or via environment variables:
    TESTJAM_URL, TESTJAM_API_KEY, TESTJAM_EXECUTION_ID

The execution must already exist in Testjam (created via API or UI).
Test cases are matched by their full Robot Framework path ("Suite.Test Name")
against TestCase.external_id, or by test name against TestCase.title.
"""

import os
from datetime import datetime, timezone
from typing import Any

try:
    import requests
except ImportError:
    raise ImportError("requests library required: pip install requests")


class TestjamListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        execution_id: str | int | None = None,
    ):
        self.url = (url or os.environ.get("TESTJAM_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("TESTJAM_API_KEY", "")
        raw_id = execution_id or os.environ.get("TESTJAM_EXECUTION_ID", "")
        self.execution_id = int(raw_id) if raw_id else None

        if not self.url:
            raise ValueError("TESTJAM_URL is required")
        if not self.api_key:
            raise ValueError("TESTJAM_API_KEY is required")
        if not self.execution_id:
            raise ValueError("TESTJAM_EXECUTION_ID is required")

        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": self.api_key})
        self._suite_path: list[str] = []
        self._kw_logs: list[str] = []
        self._result_cache: dict[str, int] | None = None

    # ─── Result index ──────────────────────────────────────────────────────────

    def _get_results(self) -> dict[str, int]:
        """Fetch execution results and build a lookup by external_id/title → result_id."""
        if self._result_cache is not None:
            return self._result_cache
        resp = self._session.get(f"{self.url}/executions/{self.execution_id}/results")
        resp.raise_for_status()
        index: dict[str, int] = {}
        for r in resp.json():
            title = (r.get("test_case_title") or "").strip().lower()
            if title:
                index[title] = r["id"]
        self._result_cache = index
        return index

    def _find_result_id(self, test_name: str, suite_path: str) -> int | None:
        index = self._get_results()
        full_path = f"{suite_path}.{test_name}".lower() if suite_path else test_name.lower()
        return index.get(full_path) or index.get(test_name.lower())

    # ─── Listener hooks ────────────────────────────────────────────────────────

    def start_suite(self, data: Any, result: Any) -> None:
        self._suite_path.append(data.name)

    def end_suite(self, data: Any, result: Any) -> None:
        if self._suite_path:
            self._suite_path.pop()

    def start_keyword(self, data: Any, result: Any) -> None:
        self._kw_logs.clear()

    def log_message(self, message: Any) -> None:
        level = getattr(message, "level", "INFO")
        text = getattr(message, "message", "")
        if text:
            self._kw_logs.append(f"**[{level}]** {text}")

    def end_test(self, data: Any, result: Any) -> None:
        suite_path = ".".join(self._suite_path[:-1]) if len(self._suite_path) > 1 else ""
        result_id = self._find_result_id(data.name, suite_path)
        if result_id is None:
            print(f"[Testjam] WARNING: no match for '{data.name}' (path: {suite_path})")
            return

        rf_status = result.status
        status_map = {"PASS": "passed", "FAIL": "failed", "SKIP": "blocked"}
        tj_status = status_map.get(rf_status, "not_run")
        duration_ms = int(result.elapsedtime) if hasattr(result, "elapsedtime") else None

        payload: dict = {
            "status": tj_status,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if result.message:
            payload["comment"] = result.message

        try:
            resp = self._session.put(f"{self.url}/results/{result_id}", json=payload)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[Testjam] ERROR updating result {result_id}: {e}")

    def close(self) -> None:
        # Mark execution as completed
        try:
            self._session.put(
                f"{self.url}/executions/{self.execution_id}",
                json={"status": "completed", "finished_at": datetime.now(timezone.utc).isoformat()},
            )
        except requests.RequestException:
            pass
