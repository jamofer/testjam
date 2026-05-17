from robot.api import logger
from robot.api.deco import keyword


class ProjectMixin:
    """Keywords covering project lifecycle."""

    @keyword("I create a project named ${name}")
    def create_project(self, name: str) -> int:
        response = self.client.post("/projects", json={"name": name})
        if response.status_code == 409 and "already exists" in response.text:
            self.current_project_id = self._lookup_project_id_by_name(name)
            logger.info(f"Reusing existing project '{name}' → id={self.current_project_id}")
            return self.current_project_id
        assert response.status_code == 201, f"Create project failed: {response.text}"
        self.current_project_id = response.json()["id"]
        logger.info(f"Created project '{name}' → id={self.current_project_id}")
        return self.current_project_id

    def _lookup_project_id_by_name(self, name: str) -> int:
        listing = self.client.get("/projects", params={"include_archived": "true"}).json()
        match = next((project for project in listing if project["name"] == name), None)
        assert match is not None, f"Project '{name}' reported as duplicate but not found in listing"
        return match["id"]

    @keyword("I rename the project to ${name}")
    def rename_project(self, name: str) -> None:
        response = self.client.put(f"/projects/{self.current_project_id}", json={"name": name})
        assert response.status_code == 200, response.text

    @keyword("I delete the project")
    def delete_project(self) -> None:
        response = self.client.delete(f"/projects/{self.current_project_id}")
        assert response.status_code == 204, response.text

    @keyword("the project name should be ${name}")
    def project_name_should_be(self, name: str) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}")
        assert response.status_code == 200
        actual = response.json()["name"]
        assert actual == name, f"Expected '{name}', got '{actual}'"

    @keyword("the project should no longer exist")
    def project_should_no_longer_exist(self) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}")
        assert response.status_code == 404, (
            f"Expected project to be gone (404), got {response.status_code}"
        )

    @keyword("I clean up the current project")
    def cleanup_current_project(self) -> None:
        if self.current_project_id is None:
            return
        self.client.delete(f"/projects/{self.current_project_id}")
        self.current_project_id = None

    @keyword("the project should have ${count} executions")
    def project_should_have_executions(self, count: str) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}")
        assert response.status_code == 200
        actual = response.json()["execution_count"]
        assert actual == int(count), f"Expected {count} executions, got {actual}"

    @keyword("I archive the project")
    def archive_project(self) -> None:
        response = self.client.post(f"/projects/{self.current_project_id}/archive")
        self.last_status_code = response.status_code

    @keyword("I unarchive the project")
    def unarchive_project(self) -> None:
        response = self.client.post(f"/projects/{self.current_project_id}/unarchive")
        self.last_status_code = response.status_code

    @keyword("the project should be archived")
    def project_should_be_archived(self) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}?include_archived=true")
        # GET on archived project still works for members; checking via list endpoint is more reliable.
        archived_listing = self.client.get("/projects?include_archived=true").json()
        match = next(p for p in archived_listing if p["id"] == self.current_project_id)
        assert match["archived_at"] is not None, "Expected project to be archived"

    @keyword("the project should not be archived")
    def project_should_not_be_archived(self) -> None:
        listing = self.client.get("/projects").json()
        match = next((p for p in listing if p["id"] == self.current_project_id), None)
        assert match is not None and match["archived_at"] is None, "Expected project to not be archived"
