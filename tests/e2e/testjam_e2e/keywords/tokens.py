from robot.api import logger
from robot.api.deco import keyword


class TokensMixin:
    """Keywords covering API token creation and authentication."""

    @keyword("I create a user token named ${name}")
    def create_user_token(self, name: str) -> str:
        resp = self.client.post("/users/me/tokens", json={"name": name})
        assert resp.status_code == 201, f"Create user token failed: {resp.text}"
        raw = resp.json()["token"]
        logger.info(f"Created user token '{name}': {resp.json()['prefix']}…")
        return raw

    @keyword("I create a project token named ${name}")
    def create_project_token(self, name: str) -> str:
        resp = self.client.post(
            f"/projects/{self.current_project_id}/tokens", json={"name": name}
        )
        assert resp.status_code == 201, f"Create project token failed: {resp.text}"
        raw = resp.json()["token"]
        logger.info(f"Created project token '{name}': {resp.json()['prefix']}…")
        return raw

    @keyword("I authenticate using token ${token}")
    def authenticate_with_token(self, token: str) -> None:
        self.client.set_api_key(token)

    @keyword("the project should have ${count} api tokens")
    def project_should_have_tokens(self, count: str) -> None:
        resp = self.client.get(f"/projects/{self.current_project_id}/tokens")
        assert resp.status_code == 200
        actual = len(resp.json())
        assert actual == int(count), f"Expected {count} tokens, got {actual}"

    @keyword("I revoke the project token named ${name}")
    def revoke_project_token(self, name: str) -> None:
        resp = self.client.get(f"/projects/{self.current_project_id}/tokens")
        tokens = {t["name"]: t["id"] for t in resp.json()}
        assert name in tokens, f"Token '{name}' not found"
        del_resp = self.client.delete(
            f"/projects/{self.current_project_id}/tokens/{tokens[name]}"
        )
        assert del_resp.status_code == 204, f"Revoke failed: {del_resp.text}"

    @keyword("I list my user tokens")
    def list_user_tokens(self) -> list:
        resp = self.client.get("/users/me/tokens")
        assert resp.status_code == 200, f"List tokens failed: {resp.text}"
        return resp.json()

    @keyword("I try to create a project token named ${name}")
    def try_create_project_token(self, name: str) -> None:
        resp = self.client.post(f"/projects/{self.current_project_id}/tokens", json={"name": name})
        self.last_status_code = resp.status_code
