from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


RUN_HEADING = 'h1'
FOCUSED_CARD = 'div.relative.border.rounded-xl:has(> span[aria-hidden="true"].bg-red-500)'
FINISH_BUTTON = 'button:has-text("Finish")'

STATUS_TO_SHORTCUT = {"passed": "p", "failed": "f", "blocked": "b", "not_run": "n"}
STATUS_LABEL = {"passed": "Pass", "failed": "Fail", "blocked": "Blocked", "not_run": "Not run"}


class ExecutionRunUIMixin:
    """Browser keywords driving the manual execution run page."""

    @keyword("I have a fresh manual run with three cases")
    def have_fresh_manual_run(self) -> None:
        self.have_fresh_project("UI-Run-Project")
        self.create_suite("Run Suite")
        self.create_case("Login flow")
        self.create_case("Checkout flow")
        self.create_case("Logout flow")
        self.start_manual_execution_for_suite("UI Run")

    @keyword("I open the run page for the current execution")
    def open_run_page(self) -> None:
        assert self.current_execution_id is not None, "No current execution set"
        BuiltIn().run_keyword(
            "Go To", f"{self.frontend_url}/executions/{self.current_execution_id}/run",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State", FOCUSED_CARD, "visible", "timeout=5s",
        )

    @keyword("I press shortcut ${key}")
    def press_shortcut(self, key: str) -> None:
        BuiltIn().run_keyword("Keyboard Key", "press", key)

    @keyword("I mark the focused result as ${status}")
    def mark_focused_as(self, status: str) -> None:
        shortcut = STATUS_TO_SHORTCUT[status]
        BuiltIn().run_keyword("Keyboard Key", "press", shortcut)
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{FOCUSED_CARD}:has-text("{STATUS_LABEL[status]}")',
            "visible", "timeout=5s",
        )

    @keyword("the focused result should be the ${position} in the list")
    def focused_result_position(self, position: str) -> None:
        index = _ordinal_to_index(position)
        cards = "div.relative.border.rounded-xl"
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{cards} >> nth={index} >> span[aria-hidden="true"].bg-red-500',
            "visible", "timeout=5s",
        )

    @keyword("the focused result status should be ${status}")
    def focused_result_status(self, status: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'{FOCUSED_CARD} >> div.rounded-full:has-text("{STATUS_LABEL[status]}")',
            "visible", "timeout=5s",
        )

    @keyword("the run summary should be passed ${passed} failed ${failed} blocked ${blocked}")
    def run_summary_should_be(self, passed: str, failed: str, blocked: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'span.text-green-600:has-text("✓ {passed} passed")', "visible", "timeout=5s",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'span.text-red-500:has-text("✗ {failed} failed")', "visible", "timeout=5s",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State",
            f'span.text-yellow-600:has-text("⚠ {blocked} blocked")', "visible", "timeout=5s",
        )

    @keyword("I finish the execution via the UI")
    def finish_execution_ui(self) -> None:
        BuiltIn().run_keyword("Click", FINISH_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State",
            'button:has-text("Completed")', "visible", "timeout=5s",
        )


def _ordinal_to_index(position: str) -> int:
    mapping = {"first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4}
    if position in mapping:
        return mapping[position]
    return int(position) - 1
