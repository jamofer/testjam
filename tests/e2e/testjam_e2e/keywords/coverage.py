from robot.api import logger
from robot.api.deco import keyword


class CoverageMixin:
    """Keywords covering the case × version coverage matrix."""

    @keyword("I record a ${status} result for the test case in version ${version}")
    def record_result_in_version(self, status: str, version: str) -> None:
        version_id = self._version_id_by_name(version)
        execution = self.client.post(
            f"/projects/{self.current_project_id}/executions",
            json={
                "title": f"Coverage {version}",
                "type": "manual",
                "version_id": version_id,
                "test_case_ids": [self.current_case_id],
            },
        )
        assert execution.status_code == 201, execution.text
        execution_id = execution.json()["id"]
        result_id = self.client.get(f"/executions/{execution_id}/results").json()[0]["id"]
        updated = self.client.put(f"/results/{result_id}", json={"status": status})
        assert updated.status_code == 200, updated.text
        logger.info(f"Recorded {status} for case {self.current_case_id} in {version}")

    @keyword("the coverage of the test case in version ${version} should be ${status}")
    def coverage_should_be(self, version: str, status: str) -> None:
        cell = self._coverage_cell(self._version_id_by_name(version))
        assert cell is not None, f"No coverage cell for version {version}"
        assert cell["status"] == status, f"Expected {status} in {version}, got {cell['status']}"

    @keyword("the test case should have no coverage in version ${version}")
    def coverage_should_be_empty(self, version: str) -> None:
        cell = self._coverage_cell(self._version_id_by_name(version))
        assert cell is None, f"Unexpected coverage in {version}: {cell}"

    @keyword("the coverage matrix should list versions ${names}")
    def coverage_should_list_versions(self, names: str) -> None:
        expected = [name.strip() for name in names.split(",")]
        listed = [version["name"] for version in self._coverage_matrix()["versions"]]
        assert sorted(listed) == sorted(expected), f"Expected versions {expected}, got {listed}"

    def _coverage_matrix(self) -> dict:
        response = self.client.get(f"/projects/{self.current_project_id}/coverage/matrix")
        assert response.status_code == 200, response.text
        return response.json()

    def _coverage_cell(self, version_id: int) -> dict | None:
        return next(
            (
                cell for cell in self._coverage_matrix()["cells"]
                if cell["case_id"] == self.current_case_id and cell["version_id"] == version_id
            ),
            None,
        )

    def _version_id_by_name(self, name: str) -> int:
        versions = self.client.get(f"/projects/{self.current_project_id}/versions").json()
        match = next((version for version in versions if version["name"] == name), None)
        assert match is not None, f"Version '{name}' not found"
        return match["id"]
