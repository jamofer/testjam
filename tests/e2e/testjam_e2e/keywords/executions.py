from robot.api import logger
from robot.api.deco import keyword


class ExecutionMixin:
    """Keywords covering test execution lifecycle and result reporting."""

    @keyword("I start an execution titled ${title}")
    def start_execution(self, title: str) -> int:
        body = {"title": title, "type": "manual"}
        response = self.client.post(
            f"/projects/{self.current_project_id}/executions",
            json=body,
        )
        assert response.status_code == 201, f"Create execution failed: {response.text}"
        self.current_execution_id = response.json()["id"]
        logger.info(f"Started execution '{title}' → id={self.current_execution_id}")
        return self.current_execution_id

    @keyword("I start an execution titled ${title} assigned to ${username}")
    def start_execution_assigned_to(self, title: str, username: str) -> int:
        assignee_id = self._resolve_user_id(username)
        body = {"title": title, "type": "manual", "assigned_to_id": assignee_id}
        response = self.client.post(
            f"/projects/{self.current_project_id}/executions",
            json=body,
        )
        assert response.status_code == 201, f"Create execution failed: {response.text}"
        self.current_execution_id = response.json()["id"]
        logger.info(
            f"Started execution '{title}' assigned to '{username}' → id={self.current_execution_id}",
        )
        return self.current_execution_id

    @keyword("I assign the execution to ${username}")
    def assign_execution_to(self, username: str) -> None:
        assignee_id = self._resolve_user_id(username)
        response = self.client.put(
            f"/executions/{self.current_execution_id}",
            json={"assigned_to_id": assignee_id},
        )
        assert response.status_code == 200, response.text

    @keyword("I start a versioned execution titled ${title}")
    def start_versioned_execution(self, title: str) -> int:
        body = {"title": title, "type": "manual", "version_id": self.current_version_id}
        response = self.client.post(
            f"/projects/{self.current_project_id}/executions",
            json=body,
        )
        assert response.status_code == 201, f"Create execution failed: {response.text}"
        self.current_execution_id = response.json()["id"]
        logger.info(f"Started versioned execution '{title}' → id={self.current_execution_id}")
        return self.current_execution_id

    @keyword("I start an execution titled ${title} for the current suite")
    def start_execution_for_suite(self, title: str) -> int:
        return self._start_for_suite(title, "automatic")

    @keyword("I start a manual execution titled ${title} for the current suite")
    def start_manual_execution_for_suite(self, title: str) -> int:
        return self._start_for_suite(title, "manual")

    def _start_for_suite(self, title: str, type_: str) -> int:
        resp = self.client.get(f"/suites/{self.current_suite_id}/cases")
        assert resp.status_code == 200
        case_ids = [c["id"] for c in resp.json()]
        body = {"title": title, "type": type_, "test_case_ids": case_ids}
        response = self.client.post(
            f"/projects/{self.current_project_id}/executions",
            json=body,
        )
        assert response.status_code == 201, f"Create execution failed: {response.text}"
        self.current_execution_id = response.json()["id"]
        return self.current_execution_id

    @keyword("I complete the execution")
    def complete_execution(self) -> None:
        self.set_execution_status("completed")

    @keyword("I abort the execution")
    def abort_execution(self) -> None:
        self.set_execution_status("aborted")

    def set_execution_status(self, status: str) -> None:
        response = self.client.put(
            f"/executions/{self.current_execution_id}",
            json={"status": status},
        )
        assert response.status_code == 200, response.text

    @keyword("I delete the execution")
    def delete_execution(self) -> None:
        response = self.client.delete(f"/executions/{self.current_execution_id}")
        assert response.status_code == 204, response.text

    @keyword("I report case ${case_id} as ${status}")
    def report_case(self, case_id: str, status: str) -> int:
        response = self.client.post(
            f"/executions/{self.current_execution_id}/results",
            json={"test_case_id": int(case_id), "status": status},
        )
        assert response.status_code == 201, f"Create result failed: {response.text}"
        result_id = response.json()["id"]
        logger.info(f"Reported case {case_id} as '{status}' → result id={result_id}")
        return result_id

    @keyword("the execution status should be ${status}")
    def execution_status_should_be(self, status: str) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}")
        assert response.status_code == 200
        actual = response.json()["status"]
        assert actual == status, f"Expected execution status '{status}', got '{actual}'"

    @keyword("the execution should no longer exist")
    def execution_should_no_longer_exist(self) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}")
        assert response.status_code == 404

    @keyword("the project should have ${count} executions")
    def project_should_have_executions(self, count: str) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}/executions")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} executions, got {actual}"

    @keyword("the execution should have ${count} results")
    def execution_should_have_results(self, count: str) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} results, got {actual}"

    @keyword("the execution version should be set")
    def execution_version_should_be_set(self) -> None:
        response = self.client.get(f"/executions/{self.current_execution_id}")
        assert response.status_code == 200
        version_id = response.json().get("version_id")
        assert version_id == self.current_version_id, (
            f"Expected version_id={self.current_version_id}, got {version_id}"
        )
