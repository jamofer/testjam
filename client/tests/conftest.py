"""Test fixtures for the Testjam client SDK.

Mirrors backend/tests/conftest.py but wires the SDK through an
``httpx.ASGITransport`` so requests never leave the process.
"""
import os

os.environ.setdefault("BCRYPT_ROUNDS", "4")
os.environ["SECRET_KEY"] = "x" * 32
os.environ["REDIS_URL"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from testjam import database as testjam_database
from testjam import main as testjam_main
import testjam.models  # noqa: F401 — register all tables on Base.metadata
from testjam.auth.security import hash_password
from testjam.core.rate_limit import limiter
from testjam.database import Base, get_db
from testjam.main import app
from testjam.models.user import User

from testjam_client import TestjamClient


limiter.enabled = False

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

testjam_database.engine = engine
testjam_database.SessionLocal = TestingSession
testjam_main.SessionLocal = TestingSession


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def _override_get_db():
    def override():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(_override_get_db) -> TestjamClient:
    with TestClient(app, base_url="http://testserver/api/v1") as http:
        sdk = TestjamClient(http=http)
        yield sdk


@pytest.fixture
def seeded_user():
    with TestingSession() as db:
        db.add(User(
            username="alice", email="alice@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=True,
        ))
        db.commit()


@pytest.fixture
def auth_client(client) -> TestjamClient:
    with TestingSession() as db:
        db.add(User(
            username="u", email="u@x.com",
            hashed_password=hash_password("pw"),
            is_active=True, is_admin=True,
        ))
        db.commit()
    client.login("u", "pw")
    return client
