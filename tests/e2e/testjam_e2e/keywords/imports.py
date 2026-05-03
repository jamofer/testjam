from robot.api import logger
from robot.api.deco import keyword


class ImportMixin:
    """Keywords covering automated result import (JUnit XML, Robot Framework output.xml)."""

    @keyword("I import JUnit results from ${file_path}")
    def import_junit(self, file_path: str) -> dict:
        with open(file_path, "rb") as fh:
            response = self.client.post(
                f"/executions/{self.current_execution_id}/results/import/junit",
                files={"file": ("results.xml", fh, "application/xml")},
            )
        assert response.status_code == 200, f"JUnit import failed: {response.text}"
        summary = response.json()
        logger.info(
            f"JUnit import: {summary.get('updated', 0)} updated, "
            f"{summary.get('errors', [])} errors"
        )
        return summary

    @keyword("I import Robot Framework results from ${file_path}")
    def import_robotframework(self, file_path: str) -> dict:
        with open(file_path, "rb") as fh:
            response = self.client.post(
                f"/executions/{self.current_execution_id}/results/import/robotframework",
                files={"file": ("output.xml", fh, "application/xml")},
            )
        assert response.status_code == 200, f"RF import failed: {response.text}"
        summary = response.json()
        logger.info(
            f"RF import: {summary.get('updated', 0)} updated, "
            f"{summary.get('errors', [])} errors"
        )
        return summary

    @keyword("the import should have updated ${count} results")
    def import_should_have_updated(self, count: str) -> None:
        assert self.last_import_summary is not None, "No import was performed yet"
        summary = self.last_import_summary
        actual = summary.get("created", 0) + summary.get("updated", 0)
        assert actual == int(count), f"Expected {count} matched results, got {actual}"

    @keyword("I import JUnit results from ${file_path} and store the summary")
    def import_junit_and_store(self, file_path: str) -> None:
        self.last_import_summary = self.import_junit(file_path)

    @keyword("I import Robot Framework results from ${file_path} and store the summary")
    def import_robotframework_and_store(self, file_path: str) -> None:
        self.last_import_summary = self.import_robotframework(file_path)
