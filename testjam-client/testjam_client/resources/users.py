"""User endpoints for the authenticated account."""
from __future__ import annotations

from testjam_client.models import User
from testjam_client.resources._base import Resource


class UsersResource(Resource):
    def me(self) -> User:
        """The user behind the current token or API key."""
        return self._request("GET", "/users/me").json()
