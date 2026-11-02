import httpx
import pytest

from testjam_client.listener.circuit_breaker import NetworkCircuitBreaker

MAX_FAILURES = 2
COOLDOWN_SECONDS = 60.0


@pytest.fixture
def server():
    return FakeServer()


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def breaker(server, clock):
    return NetworkCircuitBreaker(
        server, max_failures=MAX_FAILURES, cooldown_seconds=COOLDOWN_SECONDS, clock=clock,
    )


def test_passes_responses_through(breaker):
    assert breaker.request("GET", "/ping") == "pong"


def test_propagates_transport_failure(breaker, server):
    server.reachable = False

    with pytest.raises(httpx.ConnectError):
        breaker.request("GET", "/ping")


def test_opens_after_consecutive_failures(breaker, server):
    server.reachable = False

    _fail_requests(breaker, MAX_FAILURES + 3)

    assert server.calls == MAX_FAILURES


def test_retries_once_after_cooldown(breaker, server, clock):
    server.reachable = False
    _fail_requests(breaker, MAX_FAILURES)
    clock.now += COOLDOWN_SECONDS

    _fail_requests(breaker, 3)

    assert server.calls == MAX_FAILURES + 1


def test_success_after_cooldown_closes_breaker(breaker, server, clock):
    server.reachable = False
    _fail_requests(breaker, MAX_FAILURES)
    clock.now += COOLDOWN_SECONDS
    server.reachable = True

    breaker.request("GET", "/ping")

    server.reachable = False
    _fail_requests(breaker, MAX_FAILURES)
    assert server.calls == MAX_FAILURES + 1 + MAX_FAILURES


def test_exposes_wrapped_headers(breaker, server):
    assert breaker.headers is server.headers


def test_close_reaches_wrapped_client(breaker, server):
    breaker.close()

    assert server.closed


def _fail_requests(breaker: NetworkCircuitBreaker, count: int) -> None:
    for _ in range(count):
        with pytest.raises(httpx.ConnectError):
            breaker.request("GET", "/ping")


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class FakeServer:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.reachable = True
        self.closed = False
        self.calls = 0

    def request(self, _method: str, _url: str, **_kwargs) -> str:
        self.calls += 1
        if not self.reachable:
            raise httpx.ConnectError("connection refused")
        return "pong"

    def close(self) -> None:
        self.closed = True
