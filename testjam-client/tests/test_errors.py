import httpx
import pytest

from testjam_client import TestjamClient
from testjam_client.errors import NotFound, Redirected, Unauthorized, ValidationError

HTTPS_BASE_URL = "https://testjam.example/api/v1"


@pytest.fixture
def redirecting_client():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(301, headers={"location": f"{HTTPS_BASE_URL}{request.url.path.removeprefix('/api/v1')}"}),
    )
    http = httpx.Client(base_url="http://testjam.example/api/v1", transport=transport)
    return TestjamClient(http=http)


def test_unauthenticated_request_raises_unauthorized(client):
    with pytest.raises(Unauthorized):
        client.projects.list()


def test_get_unknown_project_raises_not_found(auth_client):
    with pytest.raises(NotFound):
        auth_client.projects.get(99999)


def test_create_project_without_name_raises_validation_error(auth_client):
    with pytest.raises(ValidationError):
        auth_client.request("POST", "/projects", json={"description": "no name"})


def test_redirect_names_the_url_to_use(redirecting_client):
    with pytest.raises(Redirected) as raised:
        redirecting_client.projects.create("Demo")

    assert raised.value.location == f"{HTTPS_BASE_URL}/projects"
    assert "use that URL as the base URL" in str(raised.value)

