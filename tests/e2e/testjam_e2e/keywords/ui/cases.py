from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


from testjam_e2e.keywords.ui.suites import _suite_header

CASE_INPUT = 'input[placeholder="Test case title…"]'
CASE_ADD_BUTTON = 'form:has(input[placeholder="Test case title…"]) button:has-text("Add")'


def _suite_add_case_button(suite_name: str) -> str:
    return f'{_suite_header(suite_name)} button:has-text("Case")'


def _case_link(name: str) -> str:
    return f'a:has-text("{name}")'


def _case_row(name: str) -> str:
    return f'li:has({_case_link(name)})'


def _case_delete(name: str) -> str:
    return f'{_case_row(name)} button:last-child'


class CasesUIMixin:
    """Browser keywords for creating and deleting test cases via the UI."""

    @keyword("I add a test case via the UI named ${case_name} under the suite ${suite_name}")
    def add_case_ui(self, case_name: str, suite_name: str) -> None:
        BuiltIn().run_keyword("Click", _suite_add_case_button(suite_name))
        BuiltIn().run_keyword(
            "Wait For Elements State", CASE_INPUT, "visible", "timeout=5s",
        )
        BuiltIn().run_keyword("Fill Text", CASE_INPUT, case_name)
        BuiltIn().run_keyword("Click", CASE_ADD_BUTTON)
        BuiltIn().run_keyword(
            "Wait For Elements State", _case_link(case_name), "visible", "timeout=5s",
        )

    @keyword("I delete the test case ${name} via the UI")
    def delete_case_ui(self, name: str) -> None:
        BuiltIn().run_keyword("Click", _case_delete(name))
        BuiltIn().run_keyword(
            "Wait For Elements State", _case_link(name), "hidden", "timeout=5s",
        )

    @keyword("the suite should list the test case ${name}")
    def suite_should_list_case(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _case_link(name), "visible", "timeout=10s",
        )

    @keyword("the suite should not list the test case ${name}")
    def suite_should_not_list_case(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Wait For Elements State", _case_link(name), "hidden", "timeout=10s",
        )
