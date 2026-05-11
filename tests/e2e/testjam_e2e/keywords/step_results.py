from robot.api import logger
from robot.api.deco import keyword


class StepResultsMixin:
    """Keywords covering the live step-result lifecycle (running → log → final)."""

    @keyword("I have a live-ready execution with one step ${action}")
    def have_live_ready_execution(self, action: str) -> None:
        self.authenticate_as_admin()
        suffix = action.replace(" ", "-")
        self.create_project(f"SR-{suffix}")
        self.create_suite("main")
        self.create_case("live")
        self.add_step(action)
        self.start_execution_for_suite("Live run")
        self.select_current_result()

    @keyword("I select the result for the current case")
    def select_current_result(self) -> int:
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        assert response.status_code == 200, response.text
        for row in response.json():
            if row["test_case_id"] == self.current_case_id:
                self.current_result_id = row["id"]
                logger.info(f"Selected result {row['id']} for case {self.current_case_id}")
                return row["id"]
        raise AssertionError(
            f"No result for case {self.current_case_id} in execution {self.current_execution_id}",
        )

    @keyword("I start a step result for step ${action}")
    def start_step_result(self, action: str) -> int:
        step_id = self._resolve_step_id(action)
        response = self.client.post(
            f"/results/{self.current_result_id}/step-results",
            json={"step_id": step_id},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        self.current_step_result_id = body["id"]
        logger.info(
            f"Started step result {body['id']} for step '{action}' (id={step_id})",
        )
        return body["id"]

    @keyword("I append a ${level} log line ${message}")
    def append_log_line(self, level: str, message: str) -> None:
        response = self.client.post(
            f"/results/{self.current_result_id}/step-results/{self.current_step_result_id}/log",
            json={"level": level, "message": message},
        )
        assert response.status_code == 200, response.text

    @keyword("I finish the current step result with status ${status}")
    def finish_current_step_result(self, status: str) -> None:
        self._update_current_step_result({"status": status})

    @keyword("I finish the current step result with status ${status} duration ${ms} ms")
    def finish_current_step_result_with_duration(self, status: str, ms: str) -> None:
        self._update_current_step_result({"status": status, "duration_ms": int(ms)})

    @keyword("the current step result should be in ${status} state")
    def current_step_result_state_should_be(self, status: str) -> None:
        body = self._fetch_current_step_result()
        assert body["status"] == status, (
            f"Expected status '{status}', got '{body['status']}'"
        )

    @keyword("the current step result should have a start timestamp")
    def current_step_result_should_have_started_at(self) -> None:
        body = self._fetch_current_step_result()
        assert body.get("started_at"), f"started_at missing on step result {body['id']}"

    @keyword("the current step result should have duration ${ms} ms")
    def current_step_result_duration_should_be(self, ms: str) -> None:
        body = self._fetch_current_step_result()
        assert body.get("duration_ms") == int(ms), (
            f"Expected duration_ms={ms}, got {body.get('duration_ms')}"
        )

    @keyword("the current step result log should contain ${text}")
    def current_step_result_log_should_contain(self, text: str) -> None:
        body = self._fetch_current_step_result()
        log_output = body.get("log_output") or ""
        assert text in log_output, f"'{text}' not in log:\n{log_output}"

    @keyword("the current step result log should have ${count} entries")
    def current_step_result_log_entries_count(self, count: str) -> None:
        body = self._fetch_current_step_result()
        log_output = body.get("log_output") or ""
        actual = 0 if not log_output else log_output.count("\n\n") + 1
        assert actual == int(count), (
            f"Expected {count} log entries, got {actual}:\n{log_output}"
        )

    @keyword("the current result should have ${count} step results")
    def current_result_should_have_step_results(self, count: str) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        assert response.status_code == 200, response.text
        for result in response.json():
            if result["id"] == self.current_result_id:
                actual = len(result.get("step_results", []))
                assert actual == int(count), (
                    f"Expected {count} step results, got {actual}"
                )
                return
        raise AssertionError(f"Result {self.current_result_id} not found")

    def _resolve_step_id(self, action: str) -> int:
        response = self.client.get(f"/cases/{self.current_case_id}/steps")
        assert response.status_code == 200, response.text
        for step in response.json():
            if step["action"] == action:
                return step["id"]
        raise AssertionError(
            f"Step '{action}' not found in case {self.current_case_id}",
        )

    def _update_current_step_result(self, payload: dict) -> None:
        response = self.client.put(
            f"/results/{self.current_result_id}/step-results/{self.current_step_result_id}",
            json=payload,
        )
        assert response.status_code == 200, response.text

    def _fetch_current_step_result(self) -> dict:
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        assert response.status_code == 200, response.text
        for result in response.json():
            if result["id"] != self.current_result_id:
                continue
            for step_result in result.get("step_results", []):
                if step_result["id"] == self.current_step_result_id:
                    return step_result
        raise AssertionError(
            f"Step result {self.current_step_result_id} not found under result {self.current_result_id}",
        )
