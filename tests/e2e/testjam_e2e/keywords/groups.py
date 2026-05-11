from robot.api import logger
from robot.api.deco import keyword


class GroupsMixin:
    """Keywords covering group lifecycle and membership."""

    @keyword("I create a group named ${name}")
    def create_group(self, name: str) -> int:
        response = self.client.post("/groups", json={"name": name})
        if response.status_code == 400 and "already exists" in response.text:
            for group in self.client.get("/groups").json():
                if group["name"] == name:
                    self.current_group_id = group["id"]
                    return group["id"]
        assert response.status_code == 201, response.text
        self.current_group_id = response.json()["id"]
        logger.info(f"Created group '{name}' → id={self.current_group_id}")
        return self.current_group_id

    @keyword("I rename the group to ${name}")
    def rename_group(self, name: str) -> None:
        response = self.client.put(f"/groups/{self.current_group_id}", json={"name": name})
        assert response.status_code == 200, response.text

    @keyword("I delete the group")
    def delete_group(self) -> None:
        response = self.client.delete(f"/groups/{self.current_group_id}")
        assert response.status_code == 204, response.text

    @keyword("I add ${username} to the current group")
    def add_user_to_group(self, username: str) -> None:
        self._post_member(username, role="member")

    @keyword("I add ${username} to the current group as ${role}")
    def add_user_to_group_with_role(self, username: str, role: str) -> None:
        self._post_member(username, role=role)

    @keyword("I remove ${username} from the current group")
    def remove_user_from_group(self, username: str) -> None:
        user_id = self._resolve_user_id(username)
        response = self.client.delete(
            f"/groups/{self.current_group_id}/members/{user_id}",
        )
        assert response.status_code == 204, response.text

    @keyword("the group name should be ${name}")
    def group_name_should_be(self, name: str) -> None:
        response = self.client.get(f"/groups/{self.current_group_id}")
        actual = response.json()["name"]
        assert actual == name, f"Expected '{name}', got '{actual}'"

    @keyword("the group should have ${count} members")
    def group_should_have_members(self, count: str) -> None:
        response = self.client.get(f"/groups/{self.current_group_id}/members")
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} members, got {actual}"

    @keyword("the group should contain ${username}")
    def group_should_contain(self, username: str) -> None:
        response = self.client.get(f"/groups/{self.current_group_id}/members")
        usernames = {member["username"] for member in response.json()}
        assert username in usernames, f"'{username}' not in {usernames}"

    @keyword("the group should no longer exist")
    def group_should_no_longer_exist(self) -> None:
        response = self.client.get(f"/groups/{self.current_group_id}")
        assert response.status_code == 404

    def _post_member(self, username: str, role: str) -> None:
        user_id = self._resolve_user_id(username)
        response = self.client.post(
            f"/groups/{self.current_group_id}/members",
            params={"user_id": user_id, "role": role},
        )
        if response.status_code == 400 and "already in group" in response.text:
            return
        assert response.status_code == 201, response.text
