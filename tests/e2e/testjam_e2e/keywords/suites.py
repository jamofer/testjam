from robot.api import logger
from robot.api.deco import keyword


class SuiteMixin:
    """Keywords covering test suite lifecycle within a project."""

    @keyword("I create a suite named ${name}")
    def create_suite(self, name: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/suites",
            json={"name": name},
        )
        assert response.status_code == 201, f"Create suite failed: {response.text}"
        self.current_suite_id = response.json()["id"]
        logger.info(f"Created suite '{name}' → id={self.current_suite_id}")
        return self.current_suite_id

    @keyword("I try to create a suite named ${name}")
    def try_create_suite(self, name: str) -> None:
        response = self.client.post(
            f"/projects/{self.current_project_id}/suites",
            json={"name": name},
        )
        self.last_status_code = response.status_code

    @keyword("I create a suite named ${name} with setup ${setup} and teardown ${teardown}")
    def create_suite_with_hooks(self, name: str, setup: str, teardown: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/suites",
            json={"name": name, "setup": setup, "teardown": teardown},
        )
        assert response.status_code == 201, f"Create suite failed: {response.text}"
        self.current_suite_id = response.json()["id"]
        logger.info(f"Created suite '{name}' → id={self.current_suite_id}")
        return self.current_suite_id

    @keyword("I rename the suite to ${name}")
    def rename_suite(self, name: str) -> None:
        response = self.client.put(f"/suites/{self.current_suite_id}", json={"name": name})
        assert response.status_code == 200, response.text

    @keyword("I delete the suite")
    def delete_suite(self) -> None:
        response = self.client.delete(f"/suites/{self.current_suite_id}")
        assert response.status_code == 204, response.text

    @keyword("the suite name should be ${name}")
    def suite_name_should_be(self, name: str) -> None:
        response = self.client.get(f"/suites/{self.current_suite_id}")
        assert response.status_code == 200
        actual = response.json()["name"]
        assert actual == name, f"Expected suite name '{name}', got '{actual}'"

    @keyword("the suite should no longer exist")
    def suite_should_no_longer_exist(self) -> None:
        response = self.client.get(f"/suites/{self.current_suite_id}")
        assert response.status_code == 404

    @keyword("the project should have ${count} suites")
    def project_should_have_suites(self, count: str) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}/suites")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} suites, got {actual}"

    @keyword("I create a sub-suite named ${name} inside the current suite")
    def create_sub_suite(self, name: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/suites",
            json={"name": name, "parent_suite_id": self.current_suite_id},
        )
        assert response.status_code == 201, f"Create sub-suite failed: {response.text}"
        self.current_sub_suite_id = response.json()["id"]
        logger.info(f"Created sub-suite '{name}' → id={self.current_sub_suite_id}")
        return self.current_sub_suite_id

    @keyword("the current suite should have ${count} child suites")
    def suite_should_have_child_suites(self, count: str) -> None:
        response = self.client.get(f"/suites/{self.current_suite_id}")
        assert response.status_code == 200
        actual = len(response.json()["child_suite_ids"])
        assert actual == int(count), f"Expected {count} child suites, got {actual}"

    @keyword("the child suites list should contain the sub-suite")
    def child_suites_list_should_contain_sub_suite(self) -> None:
        response = self.client.get(
            f"/projects/{self.current_project_id}/suites",
            params={"parent_suite_id": self.current_suite_id},
        )
        assert response.status_code == 200
        ids = [s["id"] for s in response.json()]
        assert self.current_sub_suite_id in ids, (
            f"Sub-suite {self.current_sub_suite_id} not found in children: {ids}"
        )
