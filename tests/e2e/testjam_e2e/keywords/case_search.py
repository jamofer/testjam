from robot.api import logger
from robot.api.deco import keyword


class CaseSearchMixin:
    """Keywords covering project-wide case search and tag filtering."""

    @keyword("I search project cases for ${query}")
    def search_project_cases(self, query: str) -> None:
        response = self.client.get(
            f"/projects/{self.current_project_id}/cases",
            params={"q": query},
        )
        assert response.status_code == 200, response.text
        self.last_case_search = response.json()
        logger.info(f"Search '{query}' → {len(self.last_case_search)} results")

    @keyword("I filter project cases by tag ${tag}")
    def filter_project_cases_by_tag(self, tag: str) -> None:
        response = self.client.get(
            f"/projects/{self.current_project_id}/cases",
            params={"tags": tag},
        )
        assert response.status_code == 200, response.text
        self.last_case_search = response.json()

    @keyword("the case search result should have ${count} cases")
    def search_result_should_have(self, count: str) -> None:
        actual = len(self.last_case_search or [])
        assert actual == int(count), f"Expected {count} cases, got {actual}"

    @keyword("the case search result should contain ${name}")
    def search_result_should_contain(self, name: str) -> None:
        names = {case["name"] for case in self.last_case_search or []}
        assert name in names, f"'{name}' not in {names}"

    @keyword("the case search result should not contain ${name}")
    def search_result_should_not_contain(self, name: str) -> None:
        names = {case["name"] for case in self.last_case_search or []}
        assert name not in names, f"'{name}' should not be in {names}"
