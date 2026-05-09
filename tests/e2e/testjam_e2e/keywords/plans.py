from robot.api import logger
from robot.api.deco import keyword


class PlanMixin:
    """Keywords covering test plan lifecycle within a project."""

    @keyword("I create a plan titled ${title}")
    def create_plan(self, title: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/plans",
            json={"title": title},
        )
        assert response.status_code == 201, f"Create plan failed: {response.text}"
        self.current_plan_id = response.json()["id"]
        logger.info(f"Created plan '{title}' → id={self.current_plan_id}")
        return self.current_plan_id

    @keyword("I add the current case to the plan")
    def add_current_case_to_plan(self) -> None:
        response = self.client.post(
            f"/plans/{self.current_plan_id}/cases",
            json={"case_ids": [self.current_case_id]},
        )
        assert response.status_code == 200, f"Add case to plan failed: {response.text}"

    @keyword("I add cases ${case_ids} to the plan")
    def add_cases_to_plan(self, case_ids: str) -> None:
        ids = [int(x) for x in case_ids.split(",")]
        response = self.client.post(
            f"/plans/{self.current_plan_id}/cases",
            json={"case_ids": ids},
        )
        assert response.status_code == 200, f"Add cases to plan failed: {response.text}"

    @keyword("I replace plan cases with ${case_ids}")
    def replace_plan_cases(self, case_ids: str) -> None:
        ids = [int(x) for x in case_ids.split(",")] if case_ids.strip() else []
        response = self.client.put(
            f"/plans/{self.current_plan_id}",
            json={"test_case_ids": ids},
        )
        assert response.status_code == 200, f"Update plan cases failed: {response.text}"

    @keyword("I rename the plan to ${title}")
    def rename_plan(self, title: str) -> None:
        response = self.client.put(
            f"/plans/{self.current_plan_id}",
            json={"title": title},
        )
        assert response.status_code == 200, response.text

    @keyword("I delete the plan")
    def delete_plan(self) -> None:
        response = self.client.delete(f"/plans/{self.current_plan_id}")
        assert response.status_code == 204, response.text

    @keyword("the plan title should be ${title}")
    def plan_title_should_be(self, title: str) -> None:
        response = self.client.get(f"/plans/{self.current_plan_id}")
        assert response.status_code == 200
        actual = response.json()["title"]
        assert actual == title, f"Expected plan title '{title}', got '{actual}'"

    @keyword("the plan should have ${count} cases")
    def plan_should_have_cases(self, count: str) -> None:
        response = self.client.get(f"/plans/{self.current_plan_id}")
        assert response.status_code == 200
        actual = len(response.json()["test_case_ids"])
        assert actual == int(count), f"Expected {count} cases, got {actual}"

    @keyword("the plan should contain the current case")
    def plan_should_contain_current_case(self) -> None:
        response = self.client.get(f"/plans/{self.current_plan_id}")
        assert response.status_code == 200
        ids = response.json()["test_case_ids"]
        assert self.current_case_id in ids, f"Case {self.current_case_id} not in plan ({ids})"

    @keyword("the plan should not contain the current case")
    def plan_should_not_contain_current_case(self) -> None:
        response = self.client.get(f"/plans/{self.current_plan_id}")
        assert response.status_code == 200
        ids = response.json()["test_case_ids"]
        assert self.current_case_id not in ids, f"Case {self.current_case_id} unexpectedly in plan"

    @keyword("the project should have ${count} plans")
    def project_should_have_plans(self, count: str) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}/plans")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} plans, got {actual}"

    @keyword("the plan should no longer exist")
    def plan_should_no_longer_exist(self) -> None:
        response = self.client.get(f"/plans/{self.current_plan_id}")
        assert response.status_code == 404
