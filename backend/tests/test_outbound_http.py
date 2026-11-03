import asyncio
import socket

import httpx
import pytest
from pydantic import ValidationError

from testjam.core.config import Settings, settings
from testjam.services import outbound_http
from testjam.services.integrations.base import ProviderRequestError
from testjam.services.integrations.providers.azure_devops import AzureDevOpsProvider
from testjam.services.integrations.providers.github import GitHubProvider
from testjam.services.integrations.providers.gitlab import GitLabProvider
from testjam.services.integrations.providers.jira import JiraProvider
from testjam.services.integrations.providers.openproject import OpenProjectProvider

URL = "https://target.example/hook"
PUBLIC_ADDRESS = "93.184.216.34"
OTHER_PUBLIC_ADDRESS = "93.184.216.35"
METADATA_URL = "http://169.254.169.254"

NON_PUBLIC_ADDRESSES = [
    "127.0.0.1",
    "0.0.0.0",
    "10.0.0.1",
    "172.16.0.1",
    "192.168.1.1",
    "169.254.169.254",
    "100.64.0.1",
    "224.0.0.1",
    "::1",
    "fc00::1",
    "fe80::1",
    "::ffff:10.0.0.1",
]

PUBLIC_ADDRESSES = ["93.184.216.34", "2606:4700:4700::1111"]

ALLOWED_HOST_URLS = [
    ("gitlab.corp.example", "https://gitlab.corp.example/api"),
    ("GitLab.Corp.Example", "https://gitlab.corp.example/api"),
    ("gitlab.corp.example", "https://GITLAB.corp.example/api"),
    ("gitlab.corp.example", "https://gitlab.corp.example./api"),
    ("gitlab", "http://gitlab:8080/api"),
    ("*.corp.example", "https://gitlab.corp.example/api"),
    ("*.corp.example", "https://ci.eu.corp.example/api"),
    ("10.20.0.0/16, gitlab.corp.example", "https://gitlab.corp.example/api"),
]

NOT_ALLOWED_HOST_URLS = [
    ("gitlab.corp.example", "https://jira.corp.example/api"),
    ("gitlab.corp.example", "https://gitlab.corp.example.evil.example/api"),
    ("gitlab.corp.example", "https://evilgitlab.corp.example/api"),
    ("gitlab.corp.example", "https://gitlab.corp.example@evil.example/api"),
    ("*.corp.example", "https://corp.example/api"),
    ("*.corp.example", "https://evilcorp.example/api"),
]

VALID_ALLOWED_HOSTS = [
    "",
    "10.20.0.0/16",
    "192.168.1.10",
    "fd00::/8",
    "gitlab",
    "gitlab.corp.example",
    "*.corp.example",
    " gitlab.corp.example , 10.20.0.0/16 ",
]

INVALID_ALLOWED_HOSTS = [
    "not a host",
    "*",
    "*corp.example",
    "gitlab.*",
    "https://gitlab.corp.example",
    "10.20.0.0/33",
    "10.20.1.5/16",
    "999.1.1.1",
]

PROVIDERS = [
    (GitHubProvider(), {"owner": "acme", "repo": "widgets", "api_base": METADATA_URL}),
    (GitLabProvider(), {"project": "acme/widgets", "base_url": METADATA_URL}),
    (JiraProvider(), {"base_url": METADATA_URL, "project_key": "TJ", "email": "alice@test.com"}),
    (AzureDevOpsProvider(), {"organization_url": METADATA_URL, "project": "Widgets", "work_item_type": "Bug"}),
    (OpenProjectProvider(), {"base_url": METADATA_URL, "project": "1", "type_id": 1}),
]


@pytest.fixture
def resolves_to(monkeypatch):
    def install(*addresses: str) -> None:
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 0)) for address in addresses]
        monkeypatch.setattr(outbound_http.socket, "getaddrinfo", lambda *_args, **_kwargs: records)

    return install


@pytest.fixture
def connections():
    return []


@pytest.fixture
def send(connections):
    def install(url: str) -> None:
        transport = outbound_http.GuardedTransport(_recording_transport(connections))
        with httpx.Client(transport=transport) as http:
            http.get(url)

    return install


@pytest.fixture
def allow_hosts(monkeypatch):
    def install(value: str) -> None:
        monkeypatch.setattr(settings, "OUTBOUND_ALLOWED_HOSTS", value)

    return install


@pytest.mark.parametrize("address", NON_PUBLIC_ADDRESSES)
def test_non_public_addresses_are_blocked(send, resolves_to, address):
    resolves_to(address)

    with pytest.raises(outbound_http.BlockedDestinationError):
        send(URL)


@pytest.mark.parametrize("address", PUBLIC_ADDRESSES)
def test_public_addresses_are_allowed(send, resolves_to, address):
    resolves_to(address)

    send(URL)


def test_host_with_any_non_public_address_is_blocked(send, resolves_to):
    resolves_to("93.184.216.34", "10.0.0.1")

    with pytest.raises(outbound_http.BlockedDestinationError):
        send(URL)


def test_allowed_network_opens_internal_address(send, resolves_to, allow_hosts):
    allow_hosts("10.20.0.0/16")
    resolves_to("10.20.1.5")

    send(URL)


def test_allowed_network_keeps_other_internal_addresses_blocked(send, resolves_to, allow_hosts):
    allow_hosts("10.20.0.0/16")
    resolves_to("169.254.169.254")

    with pytest.raises(outbound_http.BlockedDestinationError):
        send(URL)


@pytest.mark.parametrize("allowed,url", ALLOWED_HOST_URLS)
def test_allowed_host_opens_internal_address(send, resolves_to, allow_hosts, allowed, url):
    allow_hosts(allowed)
    resolves_to("10.20.1.5")

    send(url)


@pytest.mark.parametrize("allowed,url", NOT_ALLOWED_HOST_URLS)
def test_host_outside_the_allowed_list_stays_blocked(send, resolves_to, allow_hosts, allowed, url):
    allow_hosts(allowed)
    resolves_to("10.20.1.5")

    with pytest.raises(outbound_http.BlockedDestinationError):
        send(url)


def test_unresolvable_host_fails_as_a_connection_error(send, monkeypatch):
    def fail_resolution(*_args, **_kwargs):
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr(outbound_http.socket, "getaddrinfo", fail_resolution)

    with pytest.raises(httpx.ConnectError):
        send(URL)


def test_url_without_host_is_blocked(send):
    with pytest.raises(outbound_http.BlockedDestinationError):
        send("http://")


def test_connection_is_pinned_to_the_validated_address(send, resolves_to, connections):
    resolves_to(PUBLIC_ADDRESS)

    send("https://target.example:8443/hook?a=1")

    assert str(connections[0].url) == f"https://{PUBLIC_ADDRESS}:8443/hook?a=1"


def test_pinned_ipv6_address_is_a_valid_url(send, resolves_to, connections):
    resolves_to("2606:4700:4700::1111")

    send(URL)

    assert connections[0].url.host == "2606:4700:4700::1111"


def test_pinned_connection_keeps_the_hostname_for_tls_and_routing(send, resolves_to, connections):
    resolves_to(PUBLIC_ADDRESS)

    send(URL)

    assert connections[0].headers["Host"] == "target.example"
    assert connections[0].extensions["sni_hostname"] == "target.example"


def test_host_is_resolved_only_once_per_request(send, monkeypatch, connections):
    answers = iter([PUBLIC_ADDRESS, "169.254.169.254"])

    def rebinding_resolver(*_args, **_kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (next(answers), 0))]

    monkeypatch.setattr(outbound_http.socket, "getaddrinfo", rebinding_resolver)

    send(URL)

    assert [request.url.host for request in connections] == [PUBLIC_ADDRESS]


def test_next_address_is_tried_when_connecting_fails(resolves_to, connections):
    resolves_to(PUBLIC_ADDRESS, OTHER_PUBLIC_ADDRESS)
    transport = outbound_http.GuardedTransport(_recording_transport(connections, down={PUBLIC_ADDRESS}))

    with httpx.Client(transport=transport) as http:
        response = http.get(URL)

    assert response.status_code == 200
    assert [request.url.host for request in connections] == [PUBLIC_ADDRESS, OTHER_PUBLIC_ADDRESS]


def test_last_connection_error_is_raised_when_every_address_fails(resolves_to, connections):
    resolves_to(PUBLIC_ADDRESS, OTHER_PUBLIC_ADDRESS)
    down = {PUBLIC_ADDRESS, OTHER_PUBLIC_ADDRESS}
    transport = outbound_http.GuardedTransport(_recording_transport(connections, down=down))

    with httpx.Client(transport=transport) as http, pytest.raises(httpx.ConnectError):
        http.get(URL)


def test_allowed_host_is_left_to_the_http_client(send, resolves_to, allow_hosts, connections):
    allow_hosts("target.example")
    resolves_to("10.20.1.5")

    send(URL)

    assert connections[0].url.host == "target.example"


def test_public_ip_literal_is_not_rewritten(send, connections):
    send(f"https://{PUBLIC_ADDRESS}/hook")

    assert "sni_hostname" not in connections[0].extensions


def test_metadata_ip_literal_is_blocked(send):
    with pytest.raises(outbound_http.BlockedDestinationError):
        send(METADATA_URL)


def test_async_transport_pins_the_connection(resolves_to, connections):
    resolves_to(PUBLIC_ADDRESS)

    asyncio.run(_async_get(URL, connections))

    assert connections[0].url.host == PUBLIC_ADDRESS
    assert connections[0].extensions["sni_hostname"] == "target.example"


def test_async_transport_blocks_internal_addresses(resolves_to, connections):
    resolves_to("10.0.0.1")

    with pytest.raises(outbound_http.BlockedDestinationError):
        asyncio.run(_async_get(URL, connections))


@pytest.mark.parametrize("value", VALID_ALLOWED_HOSTS)
def test_valid_allowed_hosts_are_accepted_at_startup(value):
    Settings(SECRET_KEY="x" * 32, OUTBOUND_ALLOWED_HOSTS=value)


@pytest.mark.parametrize("value", INVALID_ALLOWED_HOSTS)
def test_invalid_allowed_hosts_are_rejected_at_startup(value):
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="x" * 32, OUTBOUND_ALLOWED_HOSTS=value)


@pytest.mark.parametrize("provider,config", PROVIDERS, ids=lambda value: type(value).__name__)
def test_integrations_refuse_internal_destinations(provider, config):
    with pytest.raises(ProviderRequestError, match="OUTBOUND_ALLOWED_HOSTS"):
        provider.health_check(config, "secret")


@pytest.mark.parametrize("provider,config", PROVIDERS, ids=lambda value: type(value).__name__)
def test_integrations_report_malformed_urls(provider, config):
    malformed = {key: "http://target.example:notaport" if value == METADATA_URL else value for key, value in config.items()}

    with pytest.raises(ProviderRequestError):
        provider.health_check(malformed, "secret")


async def _async_get(url: str, connections: list[httpx.Request]) -> None:
    transport = outbound_http.AsyncGuardedTransport(_recording_transport(connections))
    async with httpx.AsyncClient(transport=transport) as http:
        await http.get(url)


def _recording_transport(
    connections: list[httpx.Request], down: frozenset[str] | set[str] = frozenset(),
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        connections.append(request)
        if request.url.host in down:
            raise httpx.ConnectError("Connection refused", request=request)
        return httpx.Response(200)

    return httpx.MockTransport(handler)
