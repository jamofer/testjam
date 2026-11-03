from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn

COVERAGE_CELL = '[data-testid="coverage-cell"]'


class CoverageUIMixin:
    """Browser keywords driving the coverage matrix page."""

    @keyword("I open the coverage page")
    def open_coverage(self) -> None:
        BuiltIn().run_keyword(
            "Go To", f"{self.frontend_url}/projects/{self.current_project_id}/coverage",
        )
        BuiltIn().run_keyword("Wait For Elements State", f"{COVERAGE_CELL} >> nth=0", "visible", "timeout=10s")

    @keyword("the coverage cell of the test case in version ${version} should show ${status}")
    def coverage_cell_should_show(self, version: str, status: str) -> None:
        version_id = self._version_id_by_name(version)
        cell = (
            f'[data-testid="coverage-cell"][data-case-id="{self.current_case_id}"]'
            f'[data-version-id="{version_id}"]'
        )
        BuiltIn().run_keyword("Get Attribute", cell, "data-status", "==", status)
