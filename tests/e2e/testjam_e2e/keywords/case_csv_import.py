from pathlib import Path

from robot.api import logger
from robot.api.deco import keyword


class CaseCsvImportMixin:
    """Keywords covering the CSV test case import."""

    @keyword("I import test cases from ${file_path}")
    def import_cases_csv(self, file_path: str) -> None:
        path = Path(file_path)
        response = self.client.post(
            f"/projects/{self.current_project_id}/cases/import/csv",
            files={"file": (path.name, path.read_bytes(), "text/csv")},
        )
        assert response.status_code == 200, f"CSV import failed: {response.text}"
        self.last_case_import = response.json()
        logger.info(f"CSV import: {self.last_case_import}")

    @keyword("the case import should have created ${cases} cases and ${suites} suites")
    def case_import_should_have_created(self, cases: str, suites: str) -> None:
        actual = (self.last_case_import["created"], self.last_case_import["suites_created"])
        assert actual == (int(cases), int(suites)), f"Expected ({cases}, {suites}) created, got {actual}"

    @keyword("the case import should report errors on rows ${rows}")
    def case_import_should_report_errors_on(self, rows: str) -> None:
        expected = sorted(int(row) for row in rows.split(","))
        actual = sorted(error["row"] for error in self.last_case_import["errors"])
        assert actual == expected, f"Expected errors on rows {expected}, got {actual}"

    @keyword("the case import should report no errors")
    def case_import_should_report_no_errors(self) -> None:
        errors = self.last_case_import["errors"]
        assert errors == [], f"Expected no errors, got {errors}"

    @keyword("the case ${name} of suite ${suite_name} should have steps ${actions}")
    def imported_case_should_have_steps(self, name: str, suite_name: str, actions: str) -> None:
        expected = [action.strip() for action in actions.split(",")]
        case = self._case_by_name(self._suite_id_by_name(suite_name), name)
        steps = sorted(self.client.get(f"/cases/{case['id']}/steps").json(), key=lambda step: step["order"])
        actual = [step["action"] for step in steps]
        assert actual == expected, f"Case '{name}' has steps {actual}, expected {expected}"

    @keyword("the case ${name} of suite ${suite_name} should have tags ${tags}")
    def imported_case_should_have_tags(self, name: str, suite_name: str, tags: str) -> None:
        expected = sorted(tag.strip() for tag in tags.split(","))
        case = self._case_by_name(self._suite_id_by_name(suite_name), name)
        actual = sorted(case["tags"] or [])
        assert actual == expected, f"Case '{name}' has tags {actual}, expected {expected}"

    def _case_by_name(self, suite_id: int, name: str) -> dict:
        cases = self.client.get(f"/suites/{suite_id}/cases").json()
        match = next((case for case in cases if case["name"] == name), None)
        assert match is not None, f"Case '{name}' not found in suite {suite_id}"
        return match
