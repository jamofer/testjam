# Python SDK (`testjam-client`)

> Traduccion: [sdk.es.md](sdk.es.md).

`testjam-client` is the official Python SDK for the Testjam API. It also bundles the CLI and the Robot Framework listener as optional extras.

## Install

```bash
pip install testjam-client              # SDK only
pip install "testjam-client[cli]"       # SDK + testjam CLI binary
pip install "testjam-client[robot-listener]"  # SDK + Robot Framework listener
pip install "testjam-client[all]"       # everything
```

## Authentication

Three auth modes — pick the one that fits your context:

```python
from testjam_client import TestjamClient

# Bearer token (preferred for CI pipelines)
client = TestjamClient("https://testjam.example.com/api/v1", token="eyJ...")

# Per-project API key (scoped to one project, no user context)
client = TestjamClient("https://testjam.example.com/api/v1", api_key="tjk_...")

# Username + password (interactive / dev scripts)
client = TestjamClient("https://testjam.example.com/api/v1")
client.login("admin", "secret")
```

API keys are created under **Project → Members → API Tokens**. They carry a project scope — requests to a different project return 403.

## Quick start

```python
from testjam_client import TestjamClient

with TestjamClient("http://localhost:8080/api/v1") as client:
    client.login("admin", "secret")

    # Create or reuse a project
    project = client.projects.find_or_create("My Project")

    # Tag a version
    version = client.versions.find_or_create(project["id"], "v2.3.1")

    # Build the test library
    suite = client.suites.find_or_create(project["id"], "Smoke Tests")
    case = client.cases.find_or_create(suite["id"], "Login flow")
    client.cases.replace_steps(case["id"], [
        {"action": "Open login page", "expected_result": "Form visible"},
        {"action": "Submit credentials", "expected_result": "Redirect to dashboard"},
    ])

    # Run an execution
    execution = client.executions.create(
        project["id"],
        title="CI build #42",
        type="automatic",
        test_case_ids=[case["id"]],
        version_id=version["id"],
    )
```

## Resource modules

The client exposes one attribute per domain. Every method maps 1:1 to a REST endpoint.

| Module | Key methods |
|--------|-------------|
| `client.projects` | `list`, `get`, `create`, `delete`, `find_or_create` |
| `client.suites` | `list`, `create`, `find_or_create`, `descendants`, `parent_chain` |
| `client.cases` | `list`, `create`, `find_or_create`, `replace_steps`, `reconcile`, `archive` |
| `client.versions` | `list`, `create`, `find_or_create` |
| `client.environments` | `list`, `create`, `find_or_create` |
| `client.executions` | `list`, `create`, `get`, `list_results`, `upload_attachment` |
| `client.results` | `get`, `create`, `update` |
| `client.step_results` | `start`, `update`, `append_log` |
| `client.bugs` | `list`, `create`, `get_by_number`, `change_status`, `watch`, `comment` |
| `client.plans` | `list`, `create`, `add_cases` |
| `client.webhooks` | `list`, `create`, `test`, `list_deliveries` |
| `client.tokens` | `list_user_tokens`, `create_user_token`, `create_project_token` |
| `client.integrations` | `list_providers`, `create`, `report_from_result` |
| `client.public_reports` | `create`, `list`, `revoke`, `fetch_html` |
| `client.backup` | `download(path)` |

## CI integration example

Report results from a custom test runner:

```python
from testjam_client import TestjamClient

with TestjamClient(url, token=CI_TOKEN) as client:
    project = client.projects.find_or_create("Backend")
    suite = client.suites.find_or_create(project["id"], "Unit Tests")

    case_ids = []
    for test in discover_tests():
        case = client.cases.find_or_create(suite["id"], test.name)
        case_ids.append(case["id"])

    execution = client.executions.create(
        project["id"],
        title=f"Build #{os.environ['BUILD_NUMBER']}",
        type="automatic",
        test_case_ids=case_ids,
    )

    for result in run_tests():
        client.results.create(
            execution["id"],
            test_case_id=result.case_id,
            status="passed" if result.ok else "failed",
            comment=result.output,
        )
```

## Error handling

Every non-2xx response raises a typed exception:

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

## Environment variables

The SDK and CLI respect these env vars as fallbacks:

| Variable | Purpose |
|----------|---------|
| `TESTJAM_API_URL` | Base URL (e.g. `http://localhost:8080/api/v1`) |
| `TESTJAM_USER` | Username for auto-login |
| `TESTJAM_PASS` | Password for auto-login |
| `TESTJAM_API_KEY` | Project-scoped API key |
| `TESTJAM_PROJECT` | Default project name (listener + CLI) |
| `TESTJAM_CONFIG` | Override config file path (default `~/.config/testjam/config.toml`) |

## See also

- [CLI reference](cli.md) — interactive shell and scriptable commands
- [Robot Framework listener](robot-listener.md) — stream results from CI
