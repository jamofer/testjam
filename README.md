# Testjam

Web-based test management system for planning, executing, and tracking software quality assurance.

## Features

- **Test library** — Projects → Suites (nested) → Test cases with steps (action / setup / teardown), preconditions, tags, and file attachments
- **Test plans** — Group cases from multiple suites into versioned plans; link to software versions with VCS tags
- **Executions** — Manual runs with keyboard shortcuts (j/k navigation, p/f/b/n to set status) and automatic runs fed by CI
- **Import results** — JUnit XML and Robot Framework XML; matches by `external_id` or test name
- **Export reports** — Self-contained HTML report (collapsible by suite/test/step, auto-expands failures), PDF, and XLSX
- **Real-time listener** — Robot Framework listener (`contrib/testjam_listener.py`) that pushes results as tests run; E2E listener (`tests/e2e/testjam_e2e/e2e_listener.py`) for self-reporting
- **Access control** — JWT auth, per-project members with roles, scoped API tokens (`X-API-Key`)
- **Versions** — Track releases (draft → released → archived) with optional VCS tag; link executions to a version

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · SQLAlchemy (sync) · Alembic · PostgreSQL |
| Frontend | React 18 · Vite · TanStack Query · Tailwind CSS · Radix UI |
| Auth | JWT (Bearer) · scoped API tokens (X-API-Key) |
| Tests | pytest · Vitest · Robot Framework (E2E) |
| Dev environment | Docker Compose |

## Quick start

```bash
# Start all services (API on :8000, frontend on :5173)
docker compose up

# Create the first admin user
docker compose exec api python scripts/create_admin.py \
  --username admin --email admin@example.com --password secret

# API docs (Swagger UI)
open http://localhost:8000/api/docs

# App
open http://localhost:5173
```

Requires Docker and Docker Compose. No local Python or Node installation needed.

## Development

```bash
# Backend tests (SQLite in-memory, no Docker needed)
cd backend && pip install -e ".[dev]" && pytest

# Run a specific test file or test
pytest tests/test_executions.py
pytest tests/test_executions.py::test_create_execution

# Frontend tests
docker compose exec frontend npm test -- --run

# E2E tests (requires the stack running)
docker compose exec e2e robot tests/e2e/suites/

# Generate + apply a migration after model changes
docker compose exec api alembic revision --autogenerate -m "describe the change"
docker compose exec api alembic upgrade head
```

## Project structure

```
backend/
  testjam/
    auth/           JWT encode/decode, dependencies (get_current_user, require_project_access)
    models/         SQLAlchemy mapped classes
    schemas/        Pydantic v2 request/response models
    routers/        Endpoint handlers; all mount under /api/v1
  tests/            pytest suite (SQLite in-memory, autouse setup_db fixture)
  alembic/          Migration history

frontend/
  src/
    api/            Axios service modules (one per domain)
    hooks/          TanStack Query hooks wrapping api/ calls
    pages/          Route-level components
    components/
      layout/       Sidebar + AppLayout
      ui/           Radix UI primitives (Button, Dialog, Badge, …)
    lib/            Shared utilities (statusConfig, format, exportPdf)

tests/e2e/
  suites/           Robot Framework test suites (01_auth … 09_nested_suites)
  testjam_e2e/      Keywords, library, E2E listener

contrib/
  testjam_listener.py   RF listener for external test runs reporting into Testjam
```

## Model overview

```
Project
  └── TestSuite (self-referencing: parent_suite_id)
        └── TestCase
              └── TestStep
  └── TestPlan ↔ TestCase  (M2M)
  └── TestExecution
        └── TestResult
              └── TestStepResult
```

`TestExecution.type` is `manual` or `automatic`.
Statuses — execution: `pending · in_progress · completed · aborted`.
Result/step: `not_run · passed · failed · blocked`.

## Robot Framework listener

For reporting results from an external Robot Framework run into an existing execution:

```bash
robot --listener contrib/testjam_listener.TestjamListener \
      --variable TESTJAM_URL:http://localhost:8000/api/v1 \
      --variable TESTJAM_API_KEY:your-project-token \
      --variable TESTJAM_EXECUTION_ID:42 \
      tests/
```

Environment variables `TESTJAM_URL`, `TESTJAM_API_KEY`, and `TESTJAM_EXECUTION_ID` can be used instead of `--variable`.

The listener matches RF tests to Testjam cases by `external_id` (full RF path) or by test name, then pushes status, duration, and per-step log output (with millisecond timestamps) at the end of each test.

## API tokens

Scoped tokens allow CI pipelines to post results without a user login:

1. Create a token for a project: **Project → Settings → API Tokens**
2. Include the token in the `X-API-Key` header
3. The token is restricted to that project; requests to other projects return 403

## Export formats

| Format | Contents | How to generate |
|---|---|---|
| HTML | Full report — suites, tests, steps, log output. Collapsible; failures auto-expand. Self-contained single file. | Download button on Executions list or Execution detail |
| PDF | Summary table per test with status, executor, duration | Download button on Execution detail / run page |
| XLSX (execution) | One row per result | *(endpoint available, UI button pending)* |
| XLSX (test cases) | Full case library with steps, formatted by type | Download button on Project detail |

## Test counts

| Suite | Count |
|---|---|
| Backend (pytest) | 120 |
| Frontend (Vitest) | 64 |
| E2E (Robot Framework) | 12 |
