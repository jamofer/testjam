"""Typed exception hierarchy.

Every API response with a non-2xx status is mapped to a specific subclass so
callers can catch ``Conflict`` (idempotency races) or ``NotFound`` (lookups)
without inspecting raw HTTP status codes.
"""
from __future__ import annotations

from typing import Any


class TestjamError(Exception):
    """Base class for every error raised by the SDK."""

    def __init__(self, status_code: int, detail: Any = None, response: Any = None) -> None:
        self.status_code = status_code
        self.detail = detail
        self.response = response
        super().__init__(f"HTTP {status_code}: {detail!s}")


class Unauthorized(TestjamError):
    pass


class Forbidden(TestjamError):
    pass


class NotFound(TestjamError):
    pass


class Conflict(TestjamError):
    pass


class ValidationError(TestjamError):
    pass


class Locked(TestjamError):
    """HTTP 423: the account or resource is temporarily locked."""


class RateLimited(TestjamError):
    """HTTP 429: too many requests."""


class ServerError(TestjamError):
    pass


class Redirected(TestjamError):
    """HTTP 3xx: the server lives at another URL, usually https instead of http.

    Redirects are not followed because a redirected POST would lose its body;
    point the client at ``location`` instead.
    """

    def __init__(self, status_code: int, location: str | None, response: Any = None) -> None:
        self.location = location
        super().__init__(
            status_code, f"server redirected to {location}; use that URL as the base URL", response,
        )


_STATUS_MAP: dict[int, type[TestjamError]] = {
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    409: Conflict,
    422: ValidationError,
    423: Locked,
    429: RateLimited,
}


def raise_for_status(response) -> None:
    """Raise the matching :class:`TestjamError` subclass for non-2xx responses."""
    if 300 <= response.status_code < 400:
        raise Redirected(response.status_code, response.headers.get("location"), response)
    if response.status_code < 400:
        return
    detail = _extract_detail(response)
    if response.status_code >= 500:
        raise ServerError(response.status_code, detail, response)
    cls = _STATUS_MAP.get(response.status_code, TestjamError)
    raise cls(response.status_code, detail, response)


def _extract_detail(response) -> Any:
    try:
        body = response.json()
    except ValueError:
        return response.text
    if isinstance(body, dict) and "detail" in body:
        return body["detail"]
    return body
