from robot.api import logger
from robot.api.deco import keyword


class VersionMixin:
    """Keywords covering version lifecycle within a project."""

    @keyword("I create version ${name}")
    def create_version(self, name: str) -> int:
        return self.create_version_with_tag(name, vcs_tag=None)

    @keyword("I create version ${name} tagged ${vcs_tag}")
    def create_version_with_tag(self, name: str, vcs_tag: str | None = None) -> int:
        body = {"name": name, "status": "active"}
        if vcs_tag:
            body["vcs_tag"] = vcs_tag
        response = self.client.post(f"/projects/{self.current_project_id}/versions", json=body)
        assert response.status_code == 201, f"Create version failed: {response.text}"
        self.current_version_id = response.json()["id"]
        logger.info(f"Created version '{name}' → id={self.current_version_id}")
        return self.current_version_id

    @keyword("I release the version")
    def release_version(self) -> None:
        self.set_version_status("released")

    @keyword("I archive the version")
    def archive_version(self) -> None:
        self.set_version_status("archived")

    def set_version_status(self, status: str) -> None:
        response = self.client.put(f"/versions/{self.current_version_id}", json={"status": status})
        assert response.status_code == 200, response.text

    @keyword("I delete the version")
    def delete_version(self) -> None:
        response = self.client.delete(f"/versions/{self.current_version_id}")
        assert response.status_code == 204, response.text

    @keyword("the version status should be ${status}")
    def version_status_should_be(self, status: str) -> None:
        response = self.client.get(f"/versions/{self.current_version_id}")
        assert response.status_code == 200
        actual = response.json()["status"]
        assert actual == status, f"Expected version status '{status}', got '{actual}'"

    @keyword("the version should no longer exist")
    def version_should_no_longer_exist(self) -> None:
        response = self.client.get(f"/versions/{self.current_version_id}")
        assert response.status_code == 404

    @keyword("the project should have ${count} versions")
    def project_should_have_versions(self, count: str) -> None:
        response = self.client.get(f"/projects/{self.current_project_id}/versions")
        assert response.status_code == 200
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} versions, got {actual}"
