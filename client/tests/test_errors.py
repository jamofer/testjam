import pytest

from testjam_client.errors import NotFound, Unauthorized, ValidationError


def test_unauthenticated_request_raises_unauthorized(client):
    with pytest.raises(Unauthorized):
        client.projects.list()


def test_get_unknown_project_raises_not_found(auth_client):
    with pytest.raises(NotFound):
        auth_client.projects.get(99999)


def test_create_project_without_name_raises_validation_error(auth_client):
    with pytest.raises(ValidationError):
        auth_client.request("POST", "/projects", json={"description": "no name"})
