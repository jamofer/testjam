"""Keeps a Robot run reporting after its JWT expires.

The server has no refresh endpoint, so a long run signed in with a username and
password logs in again on the first 401 and repeats the rejected call once.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from testjam_client.client import HttpAdapter

LOGIN_PATH = "/auth/login"
UNAUTHORIZED = 401


class SessionRenewal:
    def __init__(self, http: HttpAdapter, *, renew: Callable[[], Any]) -> None:
        self._http = http
        self._renew = renew

    @property
    def headers(self) -> Any:
        return self._http.headers

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        response = self._http.request(method, url, **kwargs)
        if response.status_code != UNAUTHORIZED or url == LOGIN_PATH:
            return response
        self._renew()
        return self._http.request(method, url, **kwargs)

    def close(self) -> None:
        if hasattr(self._http, "close"):
            self._http.close()
