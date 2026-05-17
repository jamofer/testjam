# testjam-client

Python SDK for the Testjam REST API. Used by the Robot Framework listener,
the e2e orchestrator, and any consumer that talks to a Testjam server.

## Install

```bash
pip install -e .
```

Or pin from a local checkout:

```toml
dependencies = ["testjam-client @ file:///path/to/client"]
```

## Quick start

```python
from testjam_client import TestjamClient

with TestjamClient("http://localhost:8000/api/v1") as client:
    client.login("admin", "admin123")

    project = client.projects.find_or_create("My Project")
    version = client.versions.find_or_create(project["id"], "master-abc1234")

    suite = client.suites.find_or_create(project["id"], "Smoke Tests")
    case = client.cases.find_or_create(suite["id"], "Login flow")
    client.cases.replace_steps(case["id"], [
        {"action": "open page", "expected_result": "form visible"},
        {"action": "submit credentials", "expected_result": "redirect"},
    ])

    execution = client.executions.create(
        project["id"],
        title="CI build #42",
        type="automatic",
        test_case_ids=[case["id"]],
        version_id=version["id"],
    )
```

## Authentication

```python
# Bearer token (preferred for CI)
TestjamClient(url, token="eyJ...")

# Per-project API key
TestjamClient(url, api_key="tjk_...")

# Username + password (interactive / dev)
client = TestjamClient(url)
client.login("user", "pass")
```

## Resource modules

- `client.projects` — list, create, delete, `find_or_create`.
- `client.suites` — hierarchy: `descendants`, `parent_chain`, `path`,
  `case_ids_recursive`, `find_or_create`.
- `client.cases` — CRUD, steps (`list_steps`, `add_step`, `update_step`,
  `delete_step`, `reorder_steps`, `replace_steps`,
  `delete_steps_by_type`), archive (`archive`, `unarchive`),
  bulk reconciliation (`reconcile(suite_id, specs)`).
- `client.versions` — CRUD + `find_or_create` keyed by name.
- `client.environments` — CRUD + `find_or_create`.
- `client.executions` — CRUD + `list_results`, `upload_attachment`.
- `client.results` — `get`, `create`, `update`.
- `client.step_results` — `start`, `update`, `append_log`.

## Errors

Every non-2xx response raises a subclass of `TestjamError`:

```python
from testjam_client import NotFound, Conflict, ValidationError, Unauthorized

try:
    client.projects.get(99999)
except NotFound as exc:
    print(exc.detail)

try:
    client.projects.create("Existing")
except Conflict:
    pass
```

## Tests

Tests live in `client/tests` and run against the real FastAPI app via
`fastapi.testclient.TestClient` with SQLite in-memory:

```bash
make test-client
```
