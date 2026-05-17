from robot.api import logger
from robot.api.deco import keyword


class EnvironmentsMixin:
    """Keywords covering project environment catalog."""

    @keyword("I create environment ${name} with slug ${slug}")
    def create_environment(self, name: str, slug: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/environments",
            json={"name": name, "slug": slug},
        )
        assert response.status_code == 201, f"Create environment failed: {response.text}"
        self.current_environment_id = response.json()["id"]
        logger.info(f"Created environment '{slug}' → id={self.current_environment_id}")
        return self.current_environment_id

    @keyword("I mark the environment as default")
    def mark_environment_default(self) -> None:
        response = self.client.put(
            f"/environments/{self.current_environment_id}",
            json={"is_default": True},
        )
        assert response.status_code == 200, response.text

    @keyword("I archive the environment")
    def archive_environment(self) -> None:
        response = self.client.post(f"/environments/{self.current_environment_id}/archive")
        assert response.status_code == 200, response.text

    @keyword("I delete the environment")
    def delete_environment(self) -> int:
        response = self.client.delete(f"/environments/{self.current_environment_id}")
        self.last_status_code = response.status_code
        return response.status_code

    @keyword("the project should have ${count} environments")
    def project_should_have_environments(self, count: str) -> None:
        response = self.client.get(
            f"/projects/{self.current_project_id}/environments",
        )
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} environments, got {actual}"

    @keyword("the environment should be the default")
    def environment_should_be_default(self) -> None:
        response = self.client.get(f"/environments/{self.current_environment_id}")
        assert response.status_code == 200
        assert response.json()["is_default"] is True, response.json()

    @keyword("the environment should be archived")
    def environment_should_be_archived(self) -> None:
        response = self.client.get(f"/environments/{self.current_environment_id}")
        assert response.status_code == 200
        assert response.json()["archived_at"] is not None, response.json()

    @keyword("I start an execution targeting environment ${slug}")
    def start_execution_with_environment(self, slug: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/executions",
            json={
                "title": "Environment Run",
                "type": "manual",
                "environment": slug,
                "test_case_ids": [],
            },
        )
        assert response.status_code == 201, response.text
        self.current_execution_id = response.json()["id"]
        return self.current_execution_id
