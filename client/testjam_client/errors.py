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


class ServerError(TestjamError):
    pass


_STATUS_MAP: dict[int, type[TestjamError]] = {
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    409: Conflict,
    422: ValidationError,
}


def raise_for_status(response) -> None:
    """Raise the matching :class:`TestjamError` subclass for non-2xx responses."""
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
