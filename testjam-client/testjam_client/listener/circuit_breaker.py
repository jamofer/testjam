"""Stops a Robot run from waiting on a server that no longer answers.

Each listener event issues several HTTP calls, so an unreachable server would
otherwise cost one client timeout per call. After a few consecutive transport
failures the breaker fails immediately and only retries after a cooldown.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from testjam_client.client import HttpAdapter


class NetworkCircuitBreaker:
    def __init__(
        self,
        http: HttpAdapter,
        *,
        max_failures: int,
        cooldown_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._http = http
        self._max_failures = max_failures
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._failures = 0
        self._retry_at = 0.0

    @property
    def headers(self) -> Any:
        return self._http.headers

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        if self._is_open():
            raise httpx.ConnectError(f"Skipping {method} {url}: server unreachable")
        try:
            response = self._http.request(method, url, **kwargs)
        except httpx.TransportError:
            self._failures += 1
            self._retry_at = self._clock() + self._cooldown_seconds
            raise
        self._failures = 0
        return response

    def close(self) -> None:
        if hasattr(self._http, "close"):
            self._http.close()

    def _is_open(self) -> bool:
        return self._failures >= self._max_failures and self._clock() < self._retry_at
