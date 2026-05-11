from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


LIVE_INDICATOR = '[data-testid="live-indicator"]'
STEP_LOG_OUTPUT = '[data-testid="step-log-output"]'


def _result_card(case_name: str) -> str:
    return f'div.relative.border.rounded-xl:has(span.font-medium:text-is("{case_name}"))'


class LiveUpdatesUIMixin:
    """Backend triggers and browser assertions for live execution updates."""

    @keyword("I have a fresh manual run with one stepped case")
    def have_fresh_run_with_stepped_case(self) -> None:
        self.have_fresh_project("UI-Live-Project")
        self.create_suite("Live Suite")
        self.create_case("Smoke flow")
        self.current_step_id = self.add_step("Click login")
        self.start_manual_execution_for_suite("UI Live")
        self._populate_current_result_id()

    def _populate_current_result_id(self) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        assert response.status_code == 200, response.text
        results = response.json()
        assert results, "Execution has no results"
        self.current_result_id = results[0]["id"]

    @keyword("the live indicator should be visible")
    def live_indicator_visible(self) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", LIVE_INDICATOR, "visible", "timeout=5s",
        )

    @keyword("I expand the result card for case ${case_name}")
    def expand_result_card(self, case_name: str) -> None:
        BuiltIn().run_keyword("Click", _result_card(case_name))
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{_result_card(case_name)} >> text=Steps', "visible", "timeout=5s",
        )

    @keyword("the result card for case ${case_name} should be expanded")
    def result_card_should_be_expanded(self, case_name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{_result_card(case_name)} >> text=Steps', "visible", "timeout=5s",
        )

    @keyword("I trigger a backend ${event} for the current execution")
    def trigger_backend_event(self, event: str) -> None:
        if event == "step_result.started":
            self._start_step_result()
        elif event == "step_result.log_appended":
            self._append_step_log("Boot complete")
        else:
            raise AssertionError(f"Unknown event: {event}")

    @keyword("I append a backend log ${message} to the running step")
    def append_backend_log(self, message: str) -> None:
        self._append_step_log(message)

    def _start_step_result(self) -> None:
        response = self.client.post(
            f"/results/{self.current_result_id}/step-results",
            json={"step_id": self.current_step_id},
        )
        assert response.status_code == 201, response.text
        self.current_step_result_id = response.json()["id"]

    def _append_step_log(self, message: str) -> None:
        assert self.current_step_result_id is not None, "No running step result"
        response = self.client.post(
            f"/results/{self.current_result_id}/step-results/{self.current_step_result_id}/log",
            json={"level": "INFO", "message": message},
        )
        assert response.status_code == 200, response.text

    @keyword("the step ${order} log panel should contain ${text}")
    def step_log_should_contain(self, order: str, text: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{STEP_LOG_OUTPUT}:has-text("{text}")', "visible", "timeout=5s",
        )
