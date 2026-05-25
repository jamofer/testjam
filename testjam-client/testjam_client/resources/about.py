"""Server `/about` — build metadata for the connected instance.

Mirrors the FastAPI response. Public endpoint, no auth required, so this
resource works against an unauthenticated client too (useful for
compatibility checks before configuring credentials).
"""
from __future__ import annotations

from dataclasses import dataclass

from testjam_client.resources._base import Resource


@dataclass(frozen=True)
class ServerAbout:
    version: str
    ref: str
    commit: str
    built_at: str


class AboutResource(Resource):
    def get(self) -> ServerAbout:
        response = self._request("GET", "/about")
        return ServerAbout(**response.json())
