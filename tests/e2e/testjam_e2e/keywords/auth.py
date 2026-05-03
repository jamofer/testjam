import os

from robot.api import logger
from robot.api.deco import keyword


class AuthMixin:
    """Keywords covering authentication and identity."""

    @keyword("I log in as ${username} with password ${password}")
    def log_in(self, username: str, password: str) -> None:
        response = self.client.post_form("/auth/login", {"username": username, "password": password})
        assert response.status_code == 200, f"Login failed ({response.status_code}): {response.text}"
        token = response.json()["access_token"]
        self.client.set_bearer_token(token)
        logger.info(f"Authenticated as '{username}'")

    @keyword("I am authenticated as admin")
    def authenticate_as_admin(self) -> None:
        user = os.getenv("TESTJAM_ADMIN_USER", "admin")
        password = os.getenv("TESTJAM_ADMIN_PASS", "admin123")
        self.log_in(user, password)

    @keyword("I authenticate using api key ${api_key}")
    def authenticate_with_api_key(self, api_key: str) -> None:
        self.client.set_api_key(api_key)

    @keyword("I try to log in as ${username} with password ${password}")
    def try_log_in(self, username: str, password: str) -> None:
        """Attempts login without asserting success — use assertion keywords after."""
        response = self.client.post_form("/auth/login", {"username": username, "password": password})
        self.last_status_code = response.status_code

    @keyword("the response status should be ${expected_status}")
    def response_status_should_be(self, expected_status: str) -> None:
        assert self.last_status_code == int(expected_status), (
            f"Expected HTTP {expected_status}, got {self.last_status_code}"
        )

    @keyword("the current user should be ${username}")
    def current_user_should_be(self, username: str) -> None:
        response = self.client.get("/users/me")
        assert response.status_code == 200
        actual = response.json()["username"]
        assert actual == username, f"Expected user '{username}', got '{actual}'"
