from robot.api.deco import keyword


class ResultAssigneeMixin:
    """Keywords covering per-result assignees inside an execution."""

    @keyword("I assign the result of case ${case_id} to ${username}")
    def assign_result(self, case_id: str, username: str) -> None:
        response = self._update_assignee(case_id, self._resolve_user_id(username))
        assert response.status_code == 200, f"Assign result failed: {response.text}"

    @keyword("I try to assign the result of case ${case_id} to ${username}")
    def try_assign_result(self, case_id: str, username: str) -> None:
        self.last_status_code = self._update_assignee(case_id, self._resolve_user_id(username)).status_code

    @keyword("I unassign the result of case ${case_id}")
    def unassign_result(self, case_id: str) -> None:
        response = self._update_assignee(case_id, None)
        assert response.status_code == 200, f"Unassign result failed: {response.text}"

    @keyword("the results assigned to ${username} should be cases ${names}")
    def results_assigned_to_should_be(self, username: str, names: str) -> None:
        expected = sorted(name.strip() for name in names.split(","))
        assert self._case_titles_assigned_to(username) == expected

    @keyword("no result should be assigned to ${username}")
    def no_result_assigned_to(self, username: str) -> None:
        titles = self._case_titles_assigned_to(username)
        assert titles == [], f"Expected no results for '{username}', got {titles}"

    def _update_assignee(self, case_id: str, user_id: int | None):
        result_id = self._result_id_for_case(int(case_id))
        return self.client.put(f"/results/{result_id}", json={"assigned_to_id": user_id})

    def _result_id_for_case(self, case_id: int) -> int:
        results = self.client.get(f"/executions/{self.current_execution_id}/results").json()
        match = next((result for result in results if result["test_case_id"] == case_id), None)
        assert match is not None, f"No result for case {case_id} in execution {self.current_execution_id}"
        return match["id"]

    def _case_titles_assigned_to(self, username: str) -> list[str]:
        response = self.client.get(
            f"/executions/{self.current_execution_id}/results",
            params={"assigned_to_id": self._resolve_user_id(username)},
        )
        assert response.status_code == 200, response.text
        return sorted(result["test_case_title"] for result in response.json())
