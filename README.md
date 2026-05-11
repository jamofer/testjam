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
- **Real-time RF listener** — `testjam-listener` package streams results live as tests run
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

## Quick start (development)

Requires Docker + Docker Compose. No local Python or Node install needed.

```bash
docker compose -f docker-compose-dev.yml up
docker compose -f docker-compose-dev.yml exec api python scripts/create_admin.py \
  --username admin --email admin@example.com --password secret
```

Open http://localhost:5173. API docs at http://localhost:8000/api/docs.

The dev compose bind-mounts source code, runs Vite + uvicorn with `--reload`, bundles Mailpit on `:8025` and ships an `e2e` profile.

### Reset the database

```bash
docker compose -f docker-compose-dev.yml down -v && docker compose -f docker-compose-dev.yml up
```

---

## Production deploy

```bash
cp .env.example .env
# set POSTGRES_PASSWORD and SECRET_KEY (openssl rand -hex 32)
docker compose up -d
docker compose exec api python scripts/create_admin.py \
  --username admin --email admin@example.com --password secret
```

Brings up Postgres + API + nginx-served frontend on a single host port (`APP_PORT`, default `8080`). Point your external reverse proxy / TLS terminator at it.

---

## Tests

```bash
docker compose -f docker-compose-dev.yml exec api      pytest                      # backend
docker compose -f docker-compose-dev.yml exec frontend npm test -- --run           # frontend
docker compose -f docker-compose-dev.yml --profile e2e run --rm e2e                # E2E (RF + listener auto-wired)
```

Frontend `node_modules` lives in an anonymous Docker volume — always run `npm`/`vitest` via `docker compose -f docker-compose-dev.yml exec frontend …`, never on the host. The `e2e` service is gated by the `e2e` profile so it never runs on `docker compose -f docker-compose-dev.yml up`.

### Single file or test

```bash
docker compose -f docker-compose-dev.yml exec api pytest tests/test_executions.py::test_create_manual_execution
docker compose -f docker-compose-dev.yml exec frontend npm test -- --run __tests__/PlanDetailPage
docker compose -f docker-compose-dev.yml --profile e2e run --rm e2e robot --listener testjam_listener.TestjamListener suites/01_auth.robot
```

---

## Robot Framework listener (external CI)

`listener/` is a standalone `testjam-listener` package. It creates a fresh execution per run, discovers and syncs suites/cases/steps from the Robot tree, and streams pass/fail + per-step duration + per-line logs live.

```bash
pip install ./listener
TESTJAM_API_URL=http://localhost:8000/api/v1 \
TESTJAM_USER=admin TESTJAM_PASS=secret \
TESTJAM_PROJECT="My Project" \
robot --listener testjam_listener.TestjamListener tests/
```

Auth: `TESTJAM_USER` + `TESTJAM_PASS` (admin login) or `TESTJAM_API_KEY`. See `listener/README.md` for details.

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
