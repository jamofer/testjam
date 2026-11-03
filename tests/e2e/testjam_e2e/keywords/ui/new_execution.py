from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn

from testjam_e2e.keywords.ui.execution_run import RESULT_CARD

TITLE_INPUT = 'input[placeholder="Sprint 23 regression…"]'
CREATE_BUTTON = 'button[type="submit"]:has-text("Create & start execution")'


def _suite_checkbox(suite_name: str) -> str:
    return f'input[type="checkbox"][aria-label="Select all cases in {suite_name}"]'


class NewExecutionUIMixin:
    """Browser keywords driving the new execution form."""

    @keyword("I open the new execution page")
    def open_new_execution(self) -> None:
        BuiltIn().run_keyword(
            "Go To", f"{self.frontend_url}/projects/{self.current_project_id}/executions/new",
        )
        BuiltIn().run_keyword("Wait For Elements State", TITLE_INPUT, "visible", "timeout=10s")

    @keyword("I start a run titled ${title} with every case of the suite ${suite_name} via the UI")
    def start_run_via_ui(self, title: str, suite_name: str) -> None:
        BuiltIn().run_keyword("Fill Text", TITLE_INPUT, title)
        BuiltIn().run_keyword("Check Checkbox", _suite_checkbox(suite_name))
        BuiltIn().run_keyword("Click", CREATE_BUTTON)

    @keyword("the run page should list ${count} results")
    def run_page_should_list(self, count: str) -> None:
        BuiltIn().run_keyword("Wait For Elements State", f"{RESULT_CARD} >> nth=0", "visible", "timeout=10s")
        BuiltIn().run_keyword("Get Element Count", RESULT_CARD, "==", int(count))
