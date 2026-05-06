# Testjam

Web-based test management system for planning, executing, and tracking software quality assurance.

## Features

- **Test library** — Projects → Suites (nested) → Test cases with steps (action / setup / teardown), preconditions, tags, attachments
- **Test plans** — Group cases from multiple suites into versioned plans
- **Executions** — Manual runs with keyboard shortcuts (`j/k` navigation, `p/f/b/n` to set status) and automatic runs fed by CI
- **Import results** — JUnit XML and Robot Framework XML; matched by `external_id` or test name
- **Export reports** — Self-contained HTML (collapsible by suite/test/step, auto-expands failures), PDF, XLSX
- **Real-time RF listener** — Pushes results as tests run (`contrib/testjam_listener.py`)
- **Access control** — JWT auth, per-project members with roles, scoped API tokens (`X-API-Key`)
- **Versions** — Track releases (active → released → archived) with optional VCS tag

## Stack

| Layer            | Tech                                                    |
|------------------|---------------------------------------------------------|
| Backend          | FastAPI · SQLAlchemy (sync) · Alembic · PostgreSQL      |
| Frontend         | React 18 · Vite · TanStack Query · Tailwind · Radix UI  |
| Auth             | JWT Bearer + scoped API tokens (`X-API-Key`)            |
| Tests            | pytest · Vitest · Robot Framework (E2E)                 |
| Dev environment  | Docker Compose                                          |

---

## Quick start

Requires Docker + Docker Compose. **No local Python/Node install needed.**

```bash
# 1. Start everything (DB + auto migration + API on :8000 + frontend on :5173)
docker compose up

# 2. Create the first admin user
docker compose exec api python scripts/create_admin.py \
  --username admin --email admin@example.com --password secret

# 3. Open the app
xdg-open http://localhost:5173       # or open / start
```

The `api` container runs `alembic upgrade head` **before** booting `uvicorn`, so the schema is always migrated on `up`. No manual migration step needed.

API docs: http://localhost:8000/api/docs

---

## Common workflows

### Rebuild image (after changing dependencies or `Dockerfile`)

```bash
docker compose build api frontend
docker compose up -d api frontend
```

`docker compose up --build` rebuilds and restarts in one command.

### Add a database migration (after changing a model)

```bash
# 1. Generate the revision file
docker compose exec api alembic revision --autogenerate -m "short description"

# 2. Apply it (also auto-runs on next `docker compose up`)
docker compose exec api alembic upgrade head
```

### Reset the database from scratch

```bash
docker compose down -v       # drops the postgres volume
docker compose up            # fresh schema via alembic upgrade head
```

---

## Running tests

### Whole test battery

```bash
docker compose exec api      pytest                      # backend
docker compose exec frontend npm test -- --run           # frontend
docker compose --profile e2e run --rm e2e                # E2E (RF + listener auto-wired)
```

The `e2e` service is gated by the `e2e` profile so it never runs on `docker compose up`. The container's `command` already wires the Testjam listener — no extra args needed.

### Per platform — single file or test

```bash
# Backend file or single test
docker compose exec api pytest tests/test_executions.py
docker compose exec api pytest tests/test_executions.py::test_create_manual_execution

# Frontend file
docker compose exec frontend npm test -- --run __tests__/PlanDetailPage

# Single E2E suite
docker compose --profile e2e run --rm e2e robot --listener testjam_e2e.e2e_listener.TestjamE2EListener suites/01_auth.robot
```

> **Tip:** the frontend `node_modules` lives in an anonymous Docker volume — always run `npm`/`vitest` via `docker compose exec frontend …`, never on the host.

Current counts: **127 backend · 74 frontend · 12 E2E.**

---

## Project structure

```
backend/
  testjam/
    auth/             JWT, dependencies (get_current_user, require_project_access)
    models/           SQLAlchemy mapped classes
    schemas/          Pydantic v2 request/response
    routers/          Endpoint handlers (mounted under /api/v1)
  tests/              pytest suite (SQLite in-memory, autouse setup_db)
  alembic/            Migration history

frontend/
  src/
    api/              Axios modules (one per domain)
    hooks/            TanStack Query hooks
    pages/            Route components
    components/       layout (Sidebar/AppLayout) · ui (Radix primitives) · execution · project
    lib/              statusConfig, format, exportPdf

tests/e2e/
  suites/             Robot Framework test suites
  testjam_e2e/        Keywords, library, E2E listener

contrib/
  testjam_listener.py External RF listener for reporting into Testjam
```

## Model overview

```
Project
 ├── TestSuite (self-ref: parent_suite_id)
 │    └── TestCase
 │         └── TestStep
 ├── TestPlan ↔ TestCase  (M2M)
 └── TestExecution
      └── TestResult
           └── TestStepResult
```

`TestExecution.type`: `manual` | `automatic`.
Execution status: `pending · in_progress · completed · aborted`.
Result / step status: `not_run · passed · failed · blocked`.

---

## Robot Framework listener (external CI)

Push results from an external RF run into an existing Testjam execution:

```bash
robot --listener contrib/testjam_listener.TestjamListener \
      --variable TESTJAM_URL:http://localhost:8000/api/v1 \
      --variable TESTJAM_API_KEY:your-project-token \
      --variable TESTJAM_EXECUTION_ID:42 \
      tests/
```

Or use env vars: `TESTJAM_URL`, `TESTJAM_API_KEY`, `TESTJAM_EXECUTION_ID`.

The listener matches RF tests to Testjam cases by `external_id` (full RF path) or by test name, then pushes status, duration, and per-step log output (ms timestamps) at the end of each test.

## API tokens

Scoped tokens let CI post results without user login:

1. Create the token: **Project → Members → API Tokens**
2. Send `X-API-Key: <token>` on every request
3. Tokens are project-scoped: requests to a different project return 403

## Exports

| Format             | Contents                                                            | Where                                          |
|--------------------|---------------------------------------------------------------------|------------------------------------------------|
| HTML               | Full report — suites, tests, steps, logs. Self-contained, failures auto-expand. | Executions list / detail / run page            |
| PDF                | Summary table per test                                              | Execution detail / run page                    |
| XLSX (execution)   | One row per result                                                  | API endpoint                                   |
| XLSX (test cases)  | Full case library with steps, type-coloured                         | Project detail                                 |
