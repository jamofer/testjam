import os
import re

from robot.api import logger
from robot.api.deco import keyword


RESET_TOKEN_PATTERN = re.compile(r"/reset-password\?token=([A-Za-z0-9_\-]+)")


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
        user = os.getenv("TESTJAM_USER", "admin")
        password = os.getenv("TESTJAM_PASS", "admin123")
        self.log_in(user, password)

    @keyword("the admin locale is en")
    def force_admin_locale_english(self) -> None:
        self.authenticate_as_admin()
        response = self.client.put("/users/me", json={"locale": "en"})
        assert response.status_code == 200, (
            f"Failed to reset admin locale ({response.status_code}): {response.text}"
        )

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

    @keyword("the current user email")
    def current_user_email(self) -> str:
        response = self.client.get("/users/me")
        assert response.status_code == 200, response.text
        return response.json()["email"]

    @keyword("the current user should have admin privileges")
    def current_user_should_have_admin_privileges(self) -> None:
        response = self.client.get("/users/me")
        assert response.status_code == 200
        body = response.json()
        assert body.get("is_admin") is True, f"User '{body.get('username')}' is not an admin"

    @keyword("I request a password reset for ${email}")
    def request_password_reset(self, email: str) -> None:
        response = self.client.post("/auth/password-reset/request", json={"email": email})
        self.last_status_code = response.status_code

    @keyword("I confirm the password reset with token ${token} and password ${new_password}")
    def confirm_password_reset(self, token: str, new_password: str) -> None:
        response = self.client.post(
            "/auth/password-reset/confirm",
            json={"token": token, "new_password": new_password},
        )
        self.last_status_code = response.status_code

    @keyword("I extract the password reset token from the email to ${recipient}")
    def extract_reset_token_for(self, recipient: str) -> str:
        latest = self._latest_to(recipient)
        full = self._fetch_message(latest["ID"])
        body = (full.get("Text") or "") + (full.get("HTML") or "")
        match = RESET_TOKEN_PATTERN.search(body)
        assert match, f"No reset link found in latest email body to {recipient}"
        token = match.group(1)
        logger.info(f"Extracted reset token (prefix={token[:8]}…)")
        return token

    @keyword("I make ${count} failed login attempts as ${username}")
    def make_failed_login_attempts(self, count: str, username: str) -> None:
        for _ in range(int(count)):
            response = self.client.post_form(
                "/auth/login", {"username": username, "password": "definitely-wrong"},
            )
            self.last_status_code = response.status_code
