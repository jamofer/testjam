"""Guards server-side requests to URLs configured by project owners.

Webhooks and integrations let an owner choose where the API connects, which
would otherwise expose cloud metadata endpoints and internal services. Only
globally routable addresses are reachable by default; self-hosted targets are
opted in through ``OUTBOUND_ALLOWED_NETWORKS``.

The check resolves the host right before connecting, so a DNS record changed
between the check and the connection is not covered. Redirects are not followed
by the HTTP clients in use, so a redirect cannot bypass the check.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

from testjam.core.config import settings


class BlockedDestinationError(Exception):
    pass


def ensure_allowed_destination(url: str) -> None:
    """Raise ``BlockedDestinationError`` when ``url`` targets a non-public address.

    Hosts that do not resolve pass: the request then fails like any other DNS
    error, keeping its normal retry handling.
    """
    host = urlsplit(url).hostname
    if not host:
        raise BlockedDestinationError(f"URL has no host: {url}")
    if any(_is_blocked(address) for address in _resolve(host)):
        raise BlockedDestinationError(
            f"{host} is not a public address. Add its network to "
            "OUTBOUND_ALLOWED_NETWORKS to allow it.",
        )


def _resolve(host: str) -> list[str]:
    try:
        return [info[4][0] for info in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)]
    except socket.gaierror:
        return []


def _is_blocked(raw_address: str) -> bool:
    address = ipaddress.ip_address(raw_address)
    address = getattr(address, "ipv4_mapped", None) or address
    if any(address in network for network in settings.outbound_allowed_networks):
        return False
    return not address.is_global or address.is_multicast
