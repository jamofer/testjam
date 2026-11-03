from robot.api import logger
from robot.api.deco import keyword


class CaseCopyMixin:
    """Keywords covering single and bulk test case copies."""

    @keyword("I copy the test case into the suite ${suite_name}")
    def copy_case_into_suite(self, suite_name: str) -> None:
        target_id = self._suite_id_by_name(suite_name)
        response = self.client.post(f"/cases/{self.current_case_id}/copy", json={"target_suite_id": target_id})
        assert response.status_code == 201, response.text
        logger.info(f"Copied case {self.current_case_id} → {response.json()['id']}")

    @keyword("I bulk copy the cases of the current suite into a new suite named ${suite_name}")
    def bulk_copy_into_new_suite(self, suite_name: str) -> None:
        case_ids = self._case_ids_in_suite(self.current_suite_id)
        response = self.client.post(
            "/cases/bulk-copy", json={"case_ids": case_ids, "new_suite_name": suite_name},
        )
        assert response.status_code == 201, response.text

    @keyword("the suite ${suite_name} should contain cases ${names}")
    def suite_should_contain_cases(self, suite_name: str, names: str) -> None:
        expected = sorted(name.strip() for name in names.split(","))
        suite_id = self._suite_id_by_name(suite_name)
        cases = self.client.get(f"/suites/{suite_id}/cases").json()
        actual = sorted(case["name"] for case in cases)
        assert actual == expected, f"Suite '{suite_name}' has {actual}, expected {expected}"

    def _suite_id_by_name(self, name: str) -> int:
        suites = self.client.get(
            f"/projects/{self.current_project_id}/suites", params={"name": name, "all": "true"},
        ).json()
        match = next((suite for suite in suites if suite["name"] == name), None)
        assert match is not None, f"Suite '{name}' not found"
        return match["id"]

    def _case_ids_in_suite(self, suite_id: int) -> list[int]:
        return [case["id"] for case in self.client.get(f"/suites/{suite_id}/cases").json()]
