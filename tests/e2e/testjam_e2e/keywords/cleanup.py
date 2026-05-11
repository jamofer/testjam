from robot.api import logger
from robot.api.deco import keyword


class CleanupMixin:
    """Bulk-cleanup keywords for suite/test teardowns."""

    @keyword("I purge projects with prefix ${prefix}")
    def purge_projects(self, prefix: str) -> None:
        self.authenticate_as_admin()
        response = self.client.get("/projects")
        if response.status_code != 200:
            return
        for project in response.json():
            if project["name"].startswith(prefix):
                self.client.delete(f"/projects/{project['id']}")

    @keyword("I purge users with prefix ${prefix}")
    def purge_users(self, prefix: str) -> None:
        self.authenticate_as_admin()
        response = self.client.get("/users")
        if response.status_code != 200:
            return
        for user in response.json():
            if user["username"].startswith(prefix):
                self.client.delete(f"/users/{user['id']}")

    @keyword("I purge my personal tokens")
    def purge_my_tokens(self) -> None:
        response = self.client.get("/users/me/tokens")
        if response.status_code != 200:
            return
        for token in response.json():
            self.client.delete(f"/users/me/tokens/{token['id']}")

    @keyword("the admin personal tokens are cleaned up")
    def clean_up_admin_tokens(self) -> None:
        self.authenticate_as_admin()
        self.purge_my_tokens()

    @keyword("the settings and current project are cleaned up")
    def clean_up_settings_and_project(self) -> None:
        self.authenticate_as_admin()
        self.reset_settings()
        if self.current_project_id is not None:
            self.client.delete(f"/projects/{self.current_project_id}")
            self.current_project_id = None

    @keyword("the websocket session is cleaned up")
    def clean_up_websocket_session(self) -> None:
        self.close_websocket()
        if self.current_project_id is not None:
            self.authenticate_as_admin()
            self.client.delete(f"/projects/{self.current_project_id}")
            self.current_project_id = None
        if self.current_execution_id is not None:
            self.current_execution_id = None

    @keyword("I purge frontend test resources")
    def purge_frontend_resources(self) -> None:
        self.authenticate_as_admin()
        self.purge_my_tokens()
        self.purge_projects("UI-")
        self.purge_users("ui-")
        self.purge_users("notif-")
        self.purge_users("profile-")
        logger.info("Purged frontend test resources")

    @keyword("I tear down the frontend suite")
    def tear_down_frontend_suite(self) -> None:
        self.purge_frontend_resources()
        self.close_browser()
