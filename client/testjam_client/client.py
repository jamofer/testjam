"""Top-level :class:`TestjamClient`.

Owns the underlying HTTP client, authentication state, and acts as a namespace
for resource collections (``client.projects``, ``client.executions``, …). Use
:meth:`login` to exchange credentials for a JWT, or pass ``token=`` /
:meth:`set_api_key` when you already have one.

Tests pass ``http=fastapi.testclient.TestClient(app, base_url=...)`` so the
SDK hits the real FastAPI app in-process without sockets. Anything that
quacks like ``httpx.Client.request`` (returning an object with
``status_code``, ``json()``, ``text``, ``headers``) works.
"""
from __future__ import annotations

from typing import Any, Protocol

import httpx

from testjam_client.errors import raise_for_status
from testjam_client.resources.cases import CasesResource
from testjam_client.resources.environments import EnvironmentsResource
from testjam_client.resources.executions import ExecutionsResource
from testjam_client.resources.integrations import IntegrationsResource
from testjam_client.resources.projects import ProjectsResource
from testjam_client.resources.results import ResultsResource
from testjam_client.resources.step_results import StepResultsResource
from testjam_client.resources.suites import SuitesResource
from testjam_client.resources.versions import VersionsResource


DEFAULT_TIMEOUT_SECONDS = 30.0


class HttpAdapter(Protocol):
    headers: Any

    def request(self, method: str, url: str, **kwargs: Any) -> Any: ...


class TestjamClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        token: str | None = None,
        api_key: str | None = None,
        http: HttpAdapter | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if http is None:
            if base_url is None:
                raise ValueError("Either base_url or http must be provided")
            http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)
            self._owns_http = True
        else:
            self._owns_http = False
        self._http: HttpAdapter = http
        if token:
            self._http.headers["Authorization"] = f"Bearer {token}"
        if api_key:
            self._http.headers["X-API-Key"] = api_key

        self.projects = ProjectsResource(self)
        self.suites = SuitesResource(self)
        self.cases = CasesResource(self)
        self.versions = VersionsResource(self)
        self.environments = EnvironmentsResource(self)
        self.executions = ExecutionsResource(self)
        self.results = ResultsResource(self)
        self.step_results = StepResultsResource(self)
        self.integrations = IntegrationsResource(self)

    def login(self, username: str, password: str) -> str:
        response = self._http.request(
            "POST", "/auth/login",
            data={"username": username, "password": password},
        )
        raise_for_status(response)
        token = response.json()["access_token"]
        self._http.headers["Authorization"] = f"Bearer {token}"
        return token

    def set_api_key(self, key: str) -> None:
        self._http.headers["X-API-Key"] = key

    def set_token(self, token: str) -> None:
        self._http.headers["Authorization"] = f"Bearer {token}"

    def close(self) -> None:
        if self._owns_http and hasattr(self._http, "close"):
            self._http.close()

    def __enter__(self) -> "TestjamClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def request(self, method: str, path: str, **kwargs: Any):
        response = self._http.request(method, path, **kwargs)
        raise_for_status(response)
        return response
