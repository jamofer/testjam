"""Shared helpers for resource modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from testjam_client.errors import Conflict, raise_for_status


if TYPE_CHECKING:
    from testjam_client.client import TestjamClient


class Resource:
    """Base class binding a resource collection to its parent client."""

    def __init__(self, client: "TestjamClient") -> None:
        self._client = client

    def _http(self):
        return self._client._http

    def _request(self, method: str, path: str, **kwargs):
        response = self._http().request(method, path, **kwargs)
        raise_for_status(response)
        return response


__all__ = ["Resource", "Conflict"]
