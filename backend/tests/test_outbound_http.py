import socket

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


@pytest.mark.parametrize("address", NON_PUBLIC_ADDRESSES)
def test_non_public_addresses_are_blocked(resolves_to, address):
    resolves_to(address)

    with pytest.raises(outbound_http.BlockedDestinationError):
        outbound_http.ensure_allowed_destination(URL)


@pytest.mark.parametrize("address", PUBLIC_ADDRESSES)
def test_public_addresses_are_allowed(resolves_to, address):
    resolves_to(address)

    outbound_http.ensure_allowed_destination(URL)


def test_host_with_any_non_public_address_is_blocked(resolves_to):
    resolves_to("93.184.216.34", "10.0.0.1")

    with pytest.raises(outbound_http.BlockedDestinationError):
        outbound_http.ensure_allowed_destination(URL)


def test_allowed_network_opens_internal_address(resolves_to, monkeypatch):
    monkeypatch.setattr(settings, "OUTBOUND_ALLOWED_NETWORKS", "10.20.0.0/16")
    resolves_to("10.20.1.5")

    outbound_http.ensure_allowed_destination(URL)


def test_allowed_network_keeps_other_internal_addresses_blocked(resolves_to, monkeypatch):
    monkeypatch.setattr(settings, "OUTBOUND_ALLOWED_NETWORKS", "10.20.0.0/16")
    resolves_to("169.254.169.254")

    with pytest.raises(outbound_http.BlockedDestinationError):
        outbound_http.ensure_allowed_destination(URL)


def test_unresolvable_host_is_left_to_the_http_client(monkeypatch):
    def fail_resolution(*_args, **_kwargs):
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr(outbound_http.socket, "getaddrinfo", fail_resolution)

    outbound_http.ensure_allowed_destination(URL)


def test_url_without_host_is_blocked():
    with pytest.raises(outbound_http.BlockedDestinationError):
        outbound_http.ensure_allowed_destination("http://")


def test_invalid_allowed_network_is_rejected_at_startup():
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="x" * 32, OUTBOUND_ALLOWED_NETWORKS="not-a-network")


@pytest.mark.parametrize("provider,config", PROVIDERS, ids=lambda value: type(value).__name__)
def test_integrations_refuse_internal_destinations(provider, config):
    with pytest.raises(ProviderRequestError, match="OUTBOUND_ALLOWED_NETWORKS"):
        provider.health_check(config, "secret")
