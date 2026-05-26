# Architecture

Overview of the Testjam codebase for contributors, code reviewers, and LLM assistants.

## Repository layout

```
testjam/
├── backend/                  # FastAPI application
│   ├── testjam/
│   │   ├── auth/             # JWT + API key authentication
│   │   ├── core/             # Config, middleware, logging
│   │   ├── models/           # SQLAlchemy mapped classes
│   │   ├── routers/          # HTTP endpoint handlers
│   │   ├── schemas/          # Pydantic v2 request/response models
│   │   ├── services/         # Domain logic (stateless, DB-aware)
│   │   └── templates/        # Jinja email templates (per locale)
│   ├── alembic/              # Database migrations
│   ├── scripts/              # Admin scripts (create_admin, backup)
│   └── tests/                # pytest suite (SQLite in-memory)
├── frontend/                 # React SPA
│   └── src/
│       ├── api/              # Axios service modules (one per domain)
│       ├── hooks/            # TanStack Query wrappers
│       ├── pages/            # Route-level components
│       ├── components/       # Reusable UI (layout, ui primitives, feature panels)
│       ├── lib/              # Utilities (format, statusConfig, export)
│       ├── i18n/             # react-i18next (5 locales × 14 namespaces)
│       └── __tests__/        # Vitest suite
├── testjam-client/           # Python SDK + CLI + Robot listener
├── tests/e2e/                # Robot Framework E2E suites
├── docs/                     # User manual + architecture (this file)
└── docker-compose*.yml       # Prod and dev compose files
```

---

## Backend (`backend/testjam/`)

**Stack:** FastAPI, SQLAlchemy (sync sessions), Alembic, PostgreSQL 18.

All routers mount under `/api/v1` (configured in `core/config.py`). Several routers export two `APIRouter` instances — one nested under `/projects/{id}/...` and another flat under the resource name — both registered in `main.py`.

### Layers

```
HTTP request
  → Router (auth + validation + HTTP concerns)
    → Service (domain logic, DB queries, side effects)
      → Model (SQLAlchemy ORM)
        → Schema (Pydantic serialization)
  → HTTP response
```

Routers are thin: validate auth, parse input, delegate to services, return schema. Services own the business rules and are the only layer that touches the DB session directly.

### Auth

```
auth/
  security.py       — JWT encode/decode, bcrypt hashing
  dependencies.py   — get_current_user (Bearer), get_auth_context (Bearer + X-API-Key)
```

Two auth mechanisms:
- **JWT Bearer**: login via `POST /auth/login` (OAuth2PasswordRequestForm), token in `Authorization: Bearer <jwt>`.
- **API Key**: project-scoped tokens via `X-API-Key` header. Created under Project → Members → API Tokens. Cross-project access returns 403.

### Models (data relationships)

```
Project
 ├── TestSuite (self-ref: parent_suite_id)
 │    └── TestCase
 │         └── TestStep
 ├── TestPlan ↔ TestCase  (M2M via test_plan_cases)
 ├── TestExecution
 │    └── TestResult
 │         └── TestStepResult
 ├── Bug
 │    ├── BugComment
 │    ├── BugActivity
 │    ├── BugAttachment
 │    └── BugLink (self-ref: source ↔ target)
 ├── ProjectIntegration → IntegrationCredential
 ├── ProjectVersion
 ├── Environment
 ├── CustomFieldDefinition
 ├── Webhook → WebhookDelivery
 └── PublicReport
```

Key enums:
- `TestExecution.type`: `manual` | `automatic`
- Execution status: `pending` · `in_progress` · `completed` · `aborted`
- Result/step status: `not_run` · `passed` · `failed` · `blocked`
- Bug severity: `critical` · `high` · `medium` · `low`
- Bug status: `open` · `in_progress` · `resolved` · `closed` · `wont_fix` · `not_a_bug`

### Routers

| File | Mounts | Domain |
|------|--------|--------|
| `auth.py` | `/auth` | Login, password reset, register |
| `projects.py` | `/projects` | CRUD, archive, export |
| `suites.py` | `/projects/{id}/suites`, `/suites/{id}` | Hierarchical suites |
| `cases.py` | `/suites/{id}/cases`, `/cases/{id}` | Cases, steps, copy, bulk ops |
| `testplans.py` | `/projects/{id}/plans`, `/plans/{id}` | Plan CRUD, case assignment |
| `executions/` | `/projects/{id}/executions`, `/executions/{id}` | Runs, results, imports, exports |
| `bugs.py` | `/projects/{id}/bugs`, `/bugs/{id}` | Bug tracker, comments, links |
| `custom_fields.py` | `/projects/{id}/custom-fields` | Field definitions, reorder |
| `integrations.py` | `/projects/{id}/integrations` | External trackers (GitHub, Jira, ...) |
| `webhooks.py` | `/projects/{id}/webhooks` | Outbound event hooks |
| `members.py` | `/projects/{id}/members` | Project membership + roles |
| `tokens.py` | `/projects/{id}/tokens` | API key management |
| `versions.py` | `/projects/{id}/versions` | Release versions |
| `environments.py` | `/projects/{id}/environments` | Test environments |
| `ws.py` | `/ws/{topic}` | WebSocket real-time subscriptions |
| `admin.py`, `users.py` | `/admin`, `/users` | User management, instance settings |

### Services

Services are pure domain logic — no HTTP, no auth. They receive a `db: Session` and return models or raise `HTTPException` when validation fails.

Key services: `bug_activity` (audit trail), `bug_events`/`execution_events` (WebSocket + email notifications), `mention_resolver` (parse `@user #bug !run ~case` references), `webhook_dispatch` (HMAC-signed outbound), `custom_fields` (validation, coercion, matching), `backup`/`restore` (ZIP with dump + uploads).

### Migrations

Alembic `versions/` directory. The container runs `alembic upgrade head` on every start. After changing any model, generate a new revision:

```bash
docker compose exec api alembic revision --autogenerate -m "description"
```

### Tests

`backend/tests/` — pytest with `TestClient` (sync) against SQLite in-memory. `setup_db` fixture is `autouse=True`, drops/recreates tables per test. `auth_client` fixture creates a user and injects a valid JWT.

---

## Frontend (`frontend/src/`)

**Stack:** React 18, Vite, TanStack Query v5, Tailwind CSS, Radix UI primitives.

### Architecture

```
pages/              Route-level components (one per URL path)
  ↓ uses
hooks/              TanStack Query hooks (useQuery/useMutation wrappers)
  ↓ calls
api/                Axios service modules (one per backend domain)
  ↓ HTTP
backend API
```

JWT stored in `localStorage`, injected by the axios interceptor in `api/client.js`. All data fetching goes through TanStack Query — prefer `useQuery`/`useMutation` hooks over calling `api/` directly.

### Key directories

```
api/                One file per domain, mirrors backend routers
                    (bugs.js, testcases.js, executions.js, ...)

hooks/              TanStack Query wrappers — named use{Resource}
                    (useBugs.js, useSuites.js, useExecutions.js, ...)

pages/              Route components — one per feature area
                    (BugsPage, TestCasePage, ExecutionRunPage, ...)

components/
  layout/           Sidebar, AppLayout (wraps all authenticated pages)
  ui/               Radix UI primitives (button, dialog, select, badge, ...)
  bug/              Bug-specific panels (timeline, attachments, links)
  case/             Case-specific panels (steps, revisions, discussion)
  execution/        Execution-specific panels (result cards, step rows)
  customField/      Custom field panels, inputs, filters
  integration/      External tracker sections
  projectSettings/  Settings tabs (general, integrations, webhooks, ...)

lib/
  statusConfig.js   Single source of truth for execution/result status display
  bugConfig.js      Severity + status variants and constants
  format.js         fmtDuration, fmtTime, fmtDate, fmtDateTime, fmtRelative
  utils.js          cn() (classname merge)
```

### i18n

5 locales: `en` (default), `es`, `ca`, `gl`, `eu`. One JSON file per namespace per locale in `i18n/locales/{locale}/{namespace}.json`. Namespaces: `common`, `nav`, `auth`, `profile`, `projects`, `dashboard`, `suites`, `cases`, `plans`, `versions`, `members`, `executions`, `admin`, `ui`, `bugs`, `integrations`, `publicReports`, `customFields`, `about`, `projectSettings`.

### Shared primitives to reuse

- `EmptyState` (`components/ui/empty-state.jsx`)
- `SkeletonList` / `SkeletonText` (`skeleton.jsx`)
- `Breadcrumbs` (`breadcrumbs.jsx`)
- `SearchInput` (`search-input.jsx`)
- `ContextPanel` (`context-panel.jsx`)
- `useDebounced` hook
- `DateLabel` / `DateText` (`date-label.jsx`)
- `Badge` with variant system (`badge.jsx`)

### Tests

`frontend/src/__tests__/` — Vitest. Run via `make test-front`. `node_modules` lives in an anonymous Docker volume — always run via `make`, never on the host.

---

## Python SDK (`testjam-client/`)

```bash
pip install testjam-client              # SDK only
pip install "testjam-client[cli]"       # + CLI binary
pip install "testjam-client[robot-listener]"  # + RF listener
```

See [`docs/manual/sdk.md`](manual/sdk.md) for usage examples and [`docs/manual/cli.md`](manual/cli.md) for the CLI reference.

---

## E2E tests (`tests/e2e/`)

Robot Framework suites orchestrated in parallel (one process per leaf suite). Run via `make test-e2e`. The E2E service is gated by the `e2e` Docker Compose profile.

```
tests/e2e/
  suites/             .robot files (one per feature area)
  testjam_e2e/
    keywords/         Python keyword libraries (mixins)
    resources/        Shared .resource files
```

---

## Conventions

- All backend routers mount under `/api/v1`
- Project-scoped routes use `require_project_access(id)` — path param must be named `id`
- `statusConfig.js` is the single source of truth for status display (label, icon, badge variant)
- `format.js` exposes all date/duration formatters — reuse, don't re-implement
- Frontend tests import `../i18n` (via `__tests__/setup.js`) so `useTranslation()` resolves
