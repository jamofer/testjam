from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


def _treeitem(name: str) -> str:
    return f'[role="treeitem"][aria-label="{name}"]'


class SuiteTreeUIMixin:
    """Browser keywords for keyboard navigation of the suite tree."""

    @keyword("I have a fresh project named ${name} with three suites")
    def have_fresh_project_with_three_suites(self, name: str) -> None:
        self.have_fresh_project(name)
        for suite_name in ("Alpha", "Beta", "Gamma"):
            self.client.post(
                f"/projects/{self.current_project_id}/suites",
                json={"name": suite_name},
            )
        BuiltIn().run_keyword(
            "Reload",
        )
        BuiltIn().run_keyword(
            "Wait For Elements State",
            _treeitem("Alpha"), "visible", "timeout=5s",
        )

    @keyword("I focus the suite ${name}")
    def focus_suite(self, name: str) -> None:
        BuiltIn().run_keyword("Focus", _treeitem(name))

    @keyword("the suite ${name} should be focused")
    def suite_should_be_focused(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Get Element States", _treeitem(name), "contains", "focused",
        )

    @keyword("the suite ${name} should be expanded")
    def suite_should_be_expanded(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Get Attribute", _treeitem(name), "aria-expanded", "==", "true",
        )

    @keyword("the suite ${name} should be collapsed")
    def suite_should_be_collapsed(self, name: str) -> None:
        BuiltIn().run_keyword(
            "Get Attribute", _treeitem(name), "aria-expanded", "==", "false",
        )
