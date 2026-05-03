from robot.api import logger
from robot.api.deco import keyword


class CaseMixin:
    """Keywords covering test case and step lifecycle within a suite."""

    @keyword("I create a test case named ${name}")
    def create_case(self, name: str) -> int:
        response = self.client.post(
            f"/suites/{self.current_suite_id}/cases",
            json={"name": name, "suite_id": self.current_suite_id},
        )
        assert response.status_code == 201, f"Create case failed: {response.text}"
        self.current_case_id = response.json()["id"]
        logger.info(f"Created case '{name}' → id={self.current_case_id}")
        return self.current_case_id

    @keyword("I create a test case named ${name} with external id ${external_id}")
    def create_case_with_external_id(self, name: str, external_id: str) -> int:
        response = self.client.post(
            f"/suites/{self.current_suite_id}/cases",
            json={"name": name, "external_id": external_id, "suite_id": self.current_suite_id},
        )
        assert response.status_code == 201, f"Create case failed: {response.text}"
        self.current_case_id = response.json()["id"]
        logger.info(f"Created case '{name}' (external_id={external_id}) → id={self.current_case_id}")
        return self.current_case_id

    @keyword("I rename the test case to ${name}")
    def rename_case(self, name: str) -> None:
        response = self.client.put(f"/cases/{self.current_case_id}", json={"name": name})
        assert response.status_code == 200, response.text

    @keyword("I delete the test case")
    def delete_case(self) -> None:
        response = self.client.delete(f"/cases/{self.current_case_id}")
        assert response.status_code == 204, response.text

    @keyword("the test case name should be ${name}")
    def case_name_should_be(self, name: str) -> None:
        response = self.client.get(f"/cases/{self.current_case_id}")
        assert response.status_code == 200
        actual = response.json()["name"]
        assert actual == name, f"Expected case name '{name}', got '{actual}'"

    @keyword("the test case should no longer exist")
    def case_should_no_longer_exist(self) -> None:
        response = self.client.get(f"/cases/{self.current_case_id}")
        assert response.status_code == 404

    @keyword("the suite should have ${count} test cases")
    def suite_should_have_cases(self, count: str) -> None:
        response = self.client.get(f"/suites/{self.current_suite_id}/cases")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} cases, got {actual}"

    # ── Steps ─────────────────────────────────────────────────────────────────

    @keyword("I add a step ${action} to the test case")
    def add_step(self, action: str) -> int:
        return self.add_typed_step("action", action)

    @keyword("I add ${step_type} step ${action} to the test case")
    def add_typed_step(self, step_type: str, action: str) -> int:
        response = self.client.post(
            f"/cases/{self.current_case_id}/steps",
            json={"action": action, "step_type": step_type},
        )
        assert response.status_code == 201, f"Add step failed: {response.text}"
        step_id = response.json()["id"]
        logger.info(f"Added {step_type} step '{action}' → id={step_id}")
        return step_id

    @keyword("the test case should have ${count} steps")
    def case_should_have_steps(self, count: str) -> None:
        response = self.client.get(f"/cases/{self.current_case_id}/steps")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} steps, got {actual}"
