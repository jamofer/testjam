"""HTTP client — sole responsible for communication with the Testjam API.

No domain logic lives here: only transport-level concerns such as base URL,
session headers and serialisation helpers.
"""

import requests


class HttpClient:

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.bearer_token: str | None = None

    # ── Authentication ────────────────────────────────────────────────────────

    def set_bearer_token(self, token: str) -> None:
        self.bearer_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def set_api_key(self, api_key: str) -> None:
        self.bearer_token = None
        self.session.headers.pop("Authorization", None)
        self.session.headers.update({"X-API-Key": api_key})

    def clear_auth(self) -> None:
        self.bearer_token = None
        self.session.headers.pop("Authorization", None)
        self.session.headers.pop("X-API-Key", None)

    # ── HTTP verbs ────────────────────────────────────────────────────────────

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.session.get(self._url(path), **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.session.post(self._url(path), **kwargs)

    def post_form(self, path: str, data: dict) -> requests.Response:
        """POST with form encoding — used by OAuth2 login endpoint."""
        return self.session.post(self._url(path), data=data)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.session.put(self._url(path), **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.session.delete(self._url(path), **kwargs)

    def get_root(self, path: str, **kwargs) -> requests.Response:
        """GET a path off the API host without the /api/v1 prefix."""
        return self.session.get(f"{self._root_origin()}{path}", **kwargs)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _root_origin(self) -> str:
        without_prefix = self.base_url.removesuffix("/api/v1")
        return without_prefix or self.base_url
