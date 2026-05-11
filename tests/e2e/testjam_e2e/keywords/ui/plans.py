from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


NEW_PLAN_TRIGGER = 'button:has-text("New plan")'
PLAN_DIALOG_INPUT = 'input[placeholder="Plan title…"]'
PLAN_DIALOG_SUBMIT = 'button:has-text("Create plan")'
PLANS_HEADING = 'h1:has-text("Test Plans")'


def _plan_link(title: str) -> str:
    return f'a:has-text("{title}")'


def _plan_row(title: str) -> str:
    return f'li:has({_plan_link(title)})'


def _plan_delete(title: str) -> str:
    return f'{_plan_row(title)} button:last-child'


class PlansUIMixin:
    """Browser keywords driving the Test Plans page."""

    @keyword("I open the test plans page")
    def open_test_plans(self) -> None:
        assert self.current_project_id is not None, "No current project set"
        BuiltIn().run_keyword(
            "Go To", f"{self.frontend_url}/projects/{self.current_project_id}/plans",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State", PLANS_HEADING, "visible", "timeout=5s",
        )

    @keyword("I create a test plan via the UI titled ${title}")
    def create_plan_ui(self, title: str) -> None:
        BuiltIn().run_keyword("Click", NEW_PLAN_TRIGGER)
        BuiltIn().run_keyword(
            "Wait For Elements State", PLAN_DIALOG_INPUT, "visible", "timeout=5s",
        )
        BuiltIn().run_keyword("Fill Text", PLAN_DIALOG_INPUT, title)
        BuiltIn().run_keyword("Click", PLAN_DIALOG_SUBMIT)
        BuiltIn().run_keyword(
            "Wait For Elements State", _plan_link(title), "visible", "timeout=5s",
        )

    @keyword("I delete the test plan ${title} via the UI")
    def delete_plan_ui(self, title: str) -> None:
        BuiltIn().run_keyword("Click", _plan_delete(title))
        BuiltIn().run_keyword(
            "Wait For Elements State", _plan_link(title), "hidden", "timeout=5s",
        )

    @keyword("the test plans list should contain ${title}")
    def plans_should_contain(self, title: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _plan_link(title), "visible", "timeout=5s",
        )

    @keyword("the test plans list should not contain ${title}")
    def plans_should_not_contain(self, title: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _plan_link(title), "hidden", "timeout=5s",
        )
