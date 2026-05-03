import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from testjam.auth.security import hash_password
from testjam.database import Base, get_db
from testjam.main import app
from testjam.models.user import User

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    with TestingSession() as db:
        db.add(User(username="u", email="u@x.com", hashed_password=hash_password("pw"), is_active=True))
        db.commit()
    token = client.post("/api/v1/auth/login", data={"username": "u", "password": "pw"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def project_id(auth_client):
    return auth_client.post("/api/v1/projects", json={"name": "TestProject"}).json()["id"]


@pytest.fixture
def suite_id(auth_client, project_id):
    return auth_client.post(f"/api/v1/projects/{project_id}/suites", json={"name": "Suite A"}).json()["id"]


@pytest.fixture
def case_ids(auth_client, suite_id):
    ids = []
    for i in range(3):
        ids.append(
            auth_client.post(
                f"/api/v1/suites/{suite_id}/cases",
                json={"name": f"TC-{i}", "suite_id": suite_id},
            ).json()["id"]
        )
    return ids
