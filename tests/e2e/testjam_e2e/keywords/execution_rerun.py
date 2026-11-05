from robot.api import logger
from robot.api.deco import keyword

RERUN_ALL = "all"
RERUN_NOT_PASSED = "not_passed"


class ExecutionRerunMixin:
    """Keywords covering re-runs of a finished execution."""

    @keyword("I re-run every case of the execution")
    def rerun_all_cases(self) -> None:
        self._rerun(RERUN_ALL)

    @keyword("I re-run the cases of the execution that did not pass")
    def rerun_not_passed_cases(self) -> None:
        self._rerun(RERUN_NOT_PASSED)

    @keyword("I try to re-run the cases of the execution that did not pass")
    def try_rerun_not_passed_cases(self) -> None:
        response = self.client.post(
            f"/executions/{self.current_execution_id}/rerun", json={"cases": RERUN_NOT_PASSED},
        )
        self.last_status_code = response.status_code

    @keyword("the execution should cover cases ${names}")
    def execution_should_cover_cases(self, names: str) -> None:
        expected = sorted(name.strip() for name in names.split(","))
        actual = sorted(result["test_case_title"] for result in self._current_results())
        assert actual == expected, f"Execution covers {actual}, expected {expected}"

    @keyword("every result of the execution should be ${status}")
    def every_result_should_be(self, status: str) -> None:
        statuses = {result["status"] for result in self._current_results()}
        assert statuses == {status}, f"Expected every result to be '{status}', got {statuses}"

    @keyword("the execution should be titled ${title}")
    def execution_should_be_titled(self, title: str) -> None:
        actual = self.client.get(f"/executions/{self.current_execution_id}").json()["title"]
        assert actual == title, f"Expected title '{title}', got '{actual}'"

    def _rerun(self, cases: str) -> None:
        source_id = self.current_execution_id
        response = self.client.post(f"/executions/{source_id}/rerun", json={"cases": cases})
        assert response.status_code == 201, f"Re-run failed: {response.text}"
        self.current_execution_id = response.json()["id"]
        logger.info(f"Re-ran execution {source_id} ({cases}) → id={self.current_execution_id}")

    def _current_results(self) -> list[dict]:
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        assert response.status_code == 200, response.text
        return response.json()
