import fakeredis
import pytest
import redis

from testjam.auth import ip_throttle
from testjam.auth.lockout import LOCKOUT_DURATION_MINUTES, MAX_FAILED_LOGINS
from testjam.models.settings import AppSettings
from tests.conftest import TestingSession

ATTACKER_IP = "203.0.113.66"
FIRST_LOCK_SECONDS = LOCKOUT_DURATION_MINUTES * 60


@pytest.fixture(autouse=True)
def throttle_enabled():
    with TestingSession() as db:
        db.get(AppSettings, 1).ip_throttle_enabled = True
        db.commit()


@pytest.fixture
def redis_server():
    return fakeredis.FakeServer()


@pytest.fixture
def worker_store(redis_server):
    store = ip_throttle.RedisThrottleStore(fakeredis.FakeRedis(server=redis_server))
    ip_throttle.use_store(store)
    return store


@pytest.fixture
def other_worker_store(redis_server):
    return ip_throttle.RedisThrottleStore(fakeredis.FakeRedis(server=redis_server))


@pytest.fixture
def db():
    with TestingSession() as session:
        yield session


@pytest.fixture(params=["memory", "redis"])
def any_store(request, redis_server):
    if request.param == "memory":
        store = ip_throttle.MemoryThrottleStore()
    else:
        store = ip_throttle.RedisThrottleStore(fakeredis.FakeRedis(server=redis_server))
    ip_throttle.use_store(store)
    return store


def test_ip_locks_after_max_failures(db, any_store):
    _fail_logins(db, MAX_FAILED_LOGINS)

    assert ip_throttle.is_ip_locked(db, ATTACKER_IP)
    assert 0 < ip_throttle.seconds_until_ip_unlock(db, ATTACKER_IP) <= FIRST_LOCK_SECONDS


def test_lock_doubles_on_next_round(db, any_store):
    _fail_logins(db, MAX_FAILED_LOGINS * 2)

    assert ip_throttle.seconds_until_ip_unlock(db, ATTACKER_IP) > FIRST_LOCK_SECONDS


def test_successful_login_clears_counters(db, any_store):
    _fail_logins(db, MAX_FAILED_LOGINS)

    ip_throttle.clear_ip(ATTACKER_IP)

    assert not ip_throttle.is_ip_locked(db, ATTACKER_IP)


def test_failures_on_one_worker_lock_the_ip_on_another(db, worker_store, other_worker_store):
    _fail_logins(db, MAX_FAILED_LOGINS)

    ip_throttle.use_store(other_worker_store)

    assert ip_throttle.is_ip_locked(db, ATTACKER_IP)


def test_unreachable_redis_does_not_block_logins(db):
    ip_throttle.use_store(ip_throttle.RedisThrottleStore(UnreachableRedis()))

    _fail_logins(db, MAX_FAILED_LOGINS)

    assert not ip_throttle.is_ip_locked(db, ATTACKER_IP)


def _fail_logins(db, count: int) -> None:
    for _ in range(count):
        ip_throttle.register_ip_failure(db, ATTACKER_IP)


class UnreachableRedis:
    def __getattr__(self, _name):
        raise redis.ConnectionError("redis is down")
