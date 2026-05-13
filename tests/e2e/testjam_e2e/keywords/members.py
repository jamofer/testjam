from robot.api import logger
from robot.api.deco import keyword


class MembersMixin:
    """Keywords covering project member management."""

    @keyword("I create a user named ${username} with password ${password}")
    def create_user(self, username: str, password: str) -> int:
        resp = self.client.post("/users", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": password,
        })
        if resp.status_code == 400 and "already exists" in resp.text:
            return self._reuse_existing_user(username, password)
        assert resp.status_code == 201, f"Create user failed: {resp.text}"
        uid = resp.json()["id"]
        logger.info(f"Created user '{username}' → id={uid}")
        return uid

    def _reuse_existing_user(self, username: str, password: str) -> int:
        users = self.client.get("/users", params={"include_deleted": "true"}).json()
        existing = next((user for user in users if user["username"] == username), None)
        assert existing is not None, f"User '{username}' missing despite 'already exists'"
        if existing["deleted_at"] is not None:
            self.client.post(f"/users/{existing['id']}/restore")
        self.client.put(
            f"/users/{existing['id']}",
            json={"is_active": True, "clear_lockout": True, "password": password},
        )
        logger.info(f"User '{username}' reused (id={existing['id']})")
        return existing["id"]

    @keyword("I add ${username} as ${role} to the project")
    def add_member(self, username: str, role: str) -> None:
        uid = self._resolve_user_id(username)
        resp = self.client.post(f"/projects/{self.current_project_id}/members",
                                json={"user_id": uid, "role": role})
        assert resp.status_code == 201, f"Add member failed: {resp.text}"
        logger.info(f"Added '{username}' as {role}")

    @keyword("I try to add ${username} as ${role} to the project")
    def try_add_member(self, username: str, role: str) -> None:
        uid = self._resolve_user_id(username)
        resp = self.client.post(f"/projects/{self.current_project_id}/members",
                                json={"user_id": uid, "role": role})
        self.last_status_code = resp.status_code

    @keyword("I update ${username} role to ${role}")
    def update_member_role(self, username: str, role: str) -> None:
        uid = self._resolve_user_id(username)
        resp = self.client.put(f"/projects/{self.current_project_id}/members/{uid}",
                               json={"role": role})
        assert resp.status_code == 200, f"Update role failed: {resp.text}"

    @keyword("I remove ${username} from the project")
    def remove_member(self, username: str) -> None:
        uid = self._resolve_user_id(username)
        resp = self.client.delete(f"/projects/{self.current_project_id}/members/{uid}")
        assert resp.status_code == 204, f"Remove member failed: {resp.text}"

    @keyword("the project should have ${count} members")
    def project_should_have_members(self, count: str) -> None:
        resp = self.client.get(f"/projects/{self.current_project_id}/members")
        assert resp.status_code == 200
        actual = len(resp.json())
        assert actual == int(count), f"Expected {count} members, got {actual}"

    @keyword("${username} should have role ${role} in the project")
    def member_should_have_role(self, username: str, role: str) -> None:
        resp = self.client.get(f"/projects/{self.current_project_id}/members")
        members = {m["username"]: m["role"] for m in resp.json()}
        assert username in members, f"'{username}' is not a member"
        assert members[username] == role, f"Expected '{role}', got '{members[username]}'"

    def _resolve_user_id(self, username: str, include_deleted: bool = False) -> int:
        params = {"include_deleted": "true"} if include_deleted else None
        resp = self.client.get("/users", params=params)
        assert resp.status_code == 200
        users = {u["username"]: u["id"] for u in resp.json()}
        assert username in users, f"User '{username}' not found"
        return users[username]
