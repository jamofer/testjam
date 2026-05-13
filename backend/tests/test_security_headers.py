"""Security headers middleware applies to every response."""
from testjam.core.middleware import SECURITY_HEADERS


def test_security_headers_present_on_unauthenticated_endpoint(client):
    response = client.post("/api/v1/auth/login", data={"username": "x", "password": "y"})

    for header, value in SECURITY_HEADERS.items():
        assert response.headers.get(header) == value


def test_security_headers_present_on_authenticated_endpoint(auth_client):
    response = auth_client.get("/api/v1/users/me")

    for header, value in SECURITY_HEADERS.items():
        assert response.headers.get(header) == value


def test_csp_blocks_framing():
    assert "frame-ancestors 'none'" in SECURITY_HEADERS["Content-Security-Policy"]
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
