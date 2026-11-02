"""HTTP clients for server-side requests to URLs configured by project owners.

Webhooks and integrations let an owner choose where the API connects, which
would otherwise expose cloud metadata endpoints and internal services. Only
globally routable addresses are reachable by default; self-hosted targets are
opted in through ``OUTBOUND_ALLOWED_HOSTS``.

The transport resolves the host once, validates every address and connects to a
validated address, so a DNS answer that changes after the check is never used.
The original hostname is kept for the ``Host`` header, SNI and certificate
verification. Hostnames listed in ``OUTBOUND_ALLOWED_HOSTS`` are trusted and
resolved by the HTTP client as usual. Redirects are not followed, so they cannot
bypass the check, and environment proxies are ignored, since a proxy would
choose the address itself.
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket

import httpx

from testjam.core.config import settings

WILDCARD_PREFIX = "*"
SNI_EXTENSION = "sni_hostname"
NEXT_ADDRESS_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout)


class BlockedDestinationError(Exception):
    pass


def client(timeout: float) -> httpx.Client:
    return httpx.Client(timeout=timeout, transport=GuardedTransport())


def async_client(timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout, transport=AsyncGuardedTransport())


class GuardedTransport(httpx.BaseTransport):
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        *fallible, last = _pinned_requests(request)
        for candidate in fallible:
            try:
                return self._transport.handle_request(candidate)
            except NEXT_ADDRESS_ERRORS:
                continue
        return self._transport.handle_request(last)

    def close(self) -> None:
        self._transport.close()


class AsyncGuardedTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        *fallible, last = await asyncio.to_thread(_pinned_requests, request)
        for candidate in fallible:
            try:
                return await self._transport.handle_async_request(candidate)
            except NEXT_ADDRESS_ERRORS:
                continue
        return await self._transport.handle_async_request(last)

    async def aclose(self) -> None:
        await self._transport.aclose()


def _pinned_requests(request: httpx.Request) -> list[httpx.Request]:
    """One request per validated address, in resolver order."""
    host = _parse_host(request.url)
    if _is_allowed_host(host):
        return [request]
    addresses = _resolve(host)
    if not addresses:
        raise httpx.ConnectError(f"Could not resolve {host}", request=request)
    if any(_is_blocked(address) for address in addresses):
        raise BlockedDestinationError(
            f"{host} is not a public address. Add it to OUTBOUND_ALLOWED_HOSTS to allow it.",
        )
    if _is_ip_literal(host):
        return [request]
    return [_pin(request, host, address) for address in addresses]


def _pin(request: httpx.Request, host: str, address: str) -> httpx.Request:
    return httpx.Request(
        request.method,
        request.url.copy_with(host=address),
        headers=request.headers,
        stream=request.stream,
        extensions={**request.extensions, SNI_EXTENSION: host},
    )


def _parse_host(url: httpx.URL) -> str:
    """Use the ASCII form so the resolved name is the one on the wire."""
    host = url.raw_host.decode("ascii")
    if not host:
        raise BlockedDestinationError(f"URL has no host: {url}")
    return host


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def _is_allowed_host(host: str) -> bool:
    name = host.rstrip(".").lower()
    return any(_matches(name, pattern) for pattern in settings.outbound_allowed_host_patterns)


def _matches(name: str, pattern: str) -> bool:
    if pattern.startswith(WILDCARD_PREFIX):
        return name.endswith(pattern.removeprefix(WILDCARD_PREFIX))
    return name == pattern


def _resolve(host: str) -> list[str]:
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    return list(dict.fromkeys(record[4][0] for record in records))


def _is_blocked(raw_address: str) -> bool:
    address = ipaddress.ip_address(raw_address)
    address = getattr(address, "ipv4_mapped", None) or address
    if any(address in network for network in settings.outbound_allowed_networks):
        return False
    return not address.is_global or address.is_multicast
