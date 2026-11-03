import pytest

from testjam.core.rate_limit import BACKUP_RATE_LIMIT, EXPORT_RATE_LIMIT, IMPORT_RATE_LIMIT, limiter

LIMITED_ENDPOINTS = [
    ("GET", "/api/v1/projects/{project_id}/export", EXPORT_RATE_LIMIT),
    ("GET", "/api/v1/projects/{project_id}/cases/export/xlsx", EXPORT_RATE_LIMIT),
    ("GET", "/api/v1/executions/{execution_id}/export/xlsx", EXPORT_RATE_LIMIT),
    ("GET", "/api/v1/executions/{execution_id}/export/html", EXPORT_RATE_LIMIT),
    ("POST", "/api/v1/executions/{execution_id}/results/import/junit", IMPORT_RATE_LIMIT),
    ("POST", "/api/v1/executions/{execution_id}/results/import/robotframework", IMPORT_RATE_LIMIT),
    ("GET", "/api/v1/settings/backup", BACKUP_RATE_LIMIT),
    ("POST", "/api/v1/settings/restore?confirm=wrong", BACKUP_RATE_LIMIT),
]
UPLOAD = {"file": ("report.xml", b"<testsuite/>", "application/xml")}


@pytest.fixture
def rate_limited_client(auth_client):
    limiter.reset()
    limiter.enabled = True
    yield auth_client
    limiter.enabled = False
    limiter.reset()


@pytest.fixture
def ids(auth_client, project_id, case_ids):
    execution_id = auth_client.post(
        f"/api/v1/projects/{project_id}/executions",
        json={"title": "Run", "type": "manual", "test_case_ids": case_ids},
    ).json()["id"]
    return {"project_id": project_id, "execution_id": execution_id}


@pytest.mark.parametrize("method,path,limit", LIMITED_ENDPOINTS)
def test_heavy_endpoint_rejects_requests_over_its_limit(rate_limited_client, ids, method, path, limit):
    allowed = int(limit.split("/")[0])
    url = path.format(**ids)

    statuses = [_send(rate_limited_client, method, url).status_code for _ in range(allowed + 1)]

    assert 429 not in statuses[:allowed]
    assert statuses[allowed] == 429


def _send(client, method: str, url: str):
    if method == "POST":
        return client.post(url, files=UPLOAD)
    return client.get(url)
