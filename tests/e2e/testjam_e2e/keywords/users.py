from robot.api import logger
from robot.api.deco import keyword


class UsersMixin:
    """Keywords covering user lifecycle and self-service profile changes."""

    @keyword("I ensure user ${username} has password ${password}")
    def ensure_user_password(self, username: str, password: str) -> int:
        users = self.client.get("/users").json()
        existing = next((user for user in users if user["username"] == username), None)
        if existing is not None:
            self.client.delete(f"/users/{existing['id']}")
        return self.create_user(username, password)

    @keyword("I deactivate user ${username}")
    def deactivate_user(self, username: str) -> None:
        user_id = self._resolve_user_id(username)
        response = self.client.put(f"/users/{user_id}", json={"is_active": False})
        assert response.status_code == 200, response.text

    @keyword("I activate user ${username}")
    def activate_user(self, username: str) -> None:
        user_id = self._resolve_user_id(username)
        response = self.client.put(f"/users/{user_id}", json={"is_active": True})
        assert response.status_code == 200, response.text

    @keyword("I delete user ${username}")
    def delete_user(self, username: str) -> None:
        user_id = self._resolve_user_id(username)
        response = self.client.delete(f"/users/{user_id}")
        assert response.status_code == 204, response.text

    @keyword("I try to delete user ${username}")
    def try_delete_user(self, username: str) -> None:
        user_id = self._resolve_user_id(username)
        response = self.client.delete(f"/users/{user_id}")
        self.last_status_code = response.status_code

    @keyword("I try to deactivate user ${username}")
    def try_deactivate_user(self, username: str) -> None:
        user_id = self._resolve_user_id(username)
        response = self.client.put(f"/users/{user_id}", json={"is_active": False})
        self.last_status_code = response.status_code

    @keyword("I try to create a user named ${username} with password ${password}")
    def try_create_user(self, username: str, password: str) -> None:
        response = self.client.post(
            "/users",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": password,
            },
        )
        self.last_status_code = response.status_code

    @keyword("I change my password from ${current_password} to ${new_password}")
    def change_my_password(self, current_password: str, new_password: str) -> None:
        response = self.client.put(
            "/users/me/password",
            json={"current_password": current_password, "new_password": new_password},
        )
        assert response.status_code == 204, response.text
        logger.info("Changed my password")

    @keyword("I try to change my password from ${current_password} to ${new_password}")
    def try_change_password(self, current_password: str, new_password: str) -> None:
        response = self.client.put(
            "/users/me/password",
            json={"current_password": current_password, "new_password": new_password},
        )
        self.last_status_code = response.status_code

    @keyword("I update my email to ${email}")
    def update_my_email(self, email: str) -> None:
        response = self.client.put("/users/me", json={"email": email})
        assert response.status_code == 200, response.text

    @keyword("I update my full name to ${name}")
    def update_my_full_name(self, name: str) -> None:
        response = self.client.put("/users/me", json={"full_name": name})
        assert response.status_code == 200, response.text

    @keyword("the current user email should be ${email}")
    def current_email_should_be(self, email: str) -> None:
        response = self.client.get("/users/me")
        actual = response.json()["email"]
        assert actual == email, f"Expected '{email}', got '{actual}'"

    @keyword("the current user full name should be ${name}")
    def current_full_name_should_be(self, name: str) -> None:
        response = self.client.get("/users/me")
        actual = response.json().get("full_name")
        assert actual == name, f"Expected '{name}', got '{actual}'"

    @keyword("the user ${username} should be inactive")
    def user_should_be_inactive(self, username: str) -> None:
        body = self._user_record(username)
        assert body["is_active"] is False, f"User '{username}' is active"

    @keyword("the user ${username} should be active")
    def user_should_be_active(self, username: str) -> None:
        body = self._user_record(username)
        assert body["is_active"] is True, f"User '{username}' is inactive"

    @keyword("the user ${username} should no longer exist")
    def user_should_no_longer_exist(self, username: str) -> None:
        response = self.client.get("/users")
        usernames = {user["username"] for user in response.json()}
        assert username not in usernames, f"User '{username}' still exists"

    def _user_record(self, username: str) -> dict:
        response = self.client.get("/users")
        assert response.status_code == 200, response.text
        for user in response.json():
            if user["username"] == username:
                return user
        raise AssertionError(f"User '{username}' not found")
