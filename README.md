# Testjam

[![Backend](https://github.com/Jamofer/testjam/actions/workflows/backend.yml/badge.svg?branch=master)](https://github.com/Jamofer/testjam/actions/workflows/backend.yml)
[![Frontend](https://github.com/Jamofer/testjam/actions/workflows/frontend.yml/badge.svg?branch=master)](https://github.com/Jamofer/testjam/actions/workflows/frontend.yml)
[![E2E](https://github.com/Jamofer/testjam/actions/workflows/e2e.yml/badge.svg?branch=master)](https://github.com/Jamofer/testjam/actions/workflows/e2e.yml)

Web-based test management system for planning, executing, and tracking software quality assurance.

## Features

- **Test library** — Projects → Suites (nested) → Test cases with steps (action / setup / teardown), preconditions, tags, attachments
- **Test plans** — Group cases from multiple suites into versioned plans
- **Executions** — Manual runs with keyboard shortcuts (`j/k` navigation, `p/f/b/n` to set status) and automatic runs fed by CI
- **Import results** — JUnit XML and Robot Framework XML; matched by `external_id` or test name
- **HTML report export** — Self-contained, collapsible by suite/test/step, header tinted green on pass / red on fail, failures auto-expand, attachments rendered as links
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

Requires Docker + Docker Compose. No local Python or Node install needed.

```bash
docker compose up
docker compose exec api python scripts/create_admin.py \
  --username admin --email admin@example.com --password secret
```

Open http://localhost:5173. API docs at http://localhost:8000/api/docs.

`docker compose up` brings up Postgres, runs `alembic upgrade head`, then starts the API on `:8000` and the frontend on `:5173`.

### Reset the database

```bash
docker compose down -v && docker compose up
```

---

## Tests

```bash
docker compose exec api      pytest                      # backend
docker compose exec frontend npm test -- --run           # frontend
docker compose --profile e2e run --rm e2e                # E2E (RF + listener auto-wired)
```

Frontend `node_modules` lives in an anonymous Docker volume — always run `npm`/`vitest` via `docker compose exec frontend …`, never on the host. The `e2e` service is gated by the `e2e` profile so it never runs on `docker compose up`.

### Single file or test

```bash
docker compose exec api pytest tests/test_executions.py::test_create_manual_execution
docker compose exec frontend npm test -- --run __tests__/PlanDetailPage
docker compose --profile e2e run --rm e2e robot --listener testjam_e2e.e2e_listener.TestjamE2EListener suites/01_auth.robot
```

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

Or via env vars: `TESTJAM_URL`, `TESTJAM_API_KEY`, `TESTJAM_EXECUTION_ID`. Tests are matched to Testjam cases by `external_id` (full RF path) or by name; status, duration, and per-step log output are pushed at the end of each test.

## API tokens

**Project → Members → API Tokens** issues a project-scoped token. Send `X-API-Key: <token>` on every request. Cross-project access returns 403.

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
