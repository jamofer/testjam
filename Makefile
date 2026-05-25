COMPOSE = COMPOSE_FILE=docker-compose-dev.yml docker compose

# Rebuild trigger: image only rebuilds when one of these files changes.
# Source code is bind-mounted so day-to-day edits never need a rebuild.
BUILD_STAMP = .docker-build-stamp
BUILD_DEPS  = backend/Dockerfile backend/pyproject.toml \
              frontend/Dockerfile frontend/package.json frontend/package-lock.json

# Build metadata surfaced by GET /api/v1/about (sidebar version chip + About
# dialog). Re-evaluated on every make invocation so a `git checkout` followed
# by `make up` recreates the api container with the new branch/commit env —
# no rebuild needed since source is bind-mounted.
GIT_REF     := $(shell git describe --tags --exact-match 2>/dev/null || git rev-parse --abbrev-ref HEAD 2>/dev/null || echo dev)
GIT_COMMIT  := $(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)
BUILD_DATE  := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
export GIT_REF GIT_COMMIT BUILD_DATE

.PHONY: help up down reset rebuild admin backup build-client test test-api test-client test-cli-e2e test-orchestrator test-front test-e2e _up-api _up-front

help:
	@echo "Targets:"
	@echo "  make up           Start dev stack (rebuilds image only if Dockerfile/deps changed)"
	@echo "  make rebuild      Force rebuild of api + frontend images, then start"
	@echo "  make down         Stop dev stack"
	@echo "  make reset        Reset DB and restart"
	@echo "  make admin        Create admin user (admin / admin@example.com / admin123)"
	@echo "  make backup       Dump DB + uploads to ./backups (BACKUP_DIR, RETENTION_DAYS env)"
	@echo "  make build-client Build testjam-client sdist + wheel under testjam-client/dist/"
	@echo "  make test         Run backend + frontend + e2e (boots what it needs)"
	@echo "  make test-api     pytest        ARGS=path/to/test"
	@echo "  make test-client  pytest /testjam-client/tests — SDK + listener + CLI tests run in api container"
	@echo "  make test-cli-e2e CLI smoke against the running api (creates admin if needed)"
	@echo "  make test-orchestrator pytest tests/e2e/orchestrator/tests"
	@echo "  make test-front   vitest        ARGS=__tests__/Foo"
	@echo "  make test-e2e     orchestrator launches 1 robot subprocess per leaf suite (parallel)"
	@echo "                    ARGS=\"-s '01 Auth'\" filter by suite name or glob"
	@echo "                    ARGS=\"-s '*.Api Server.*'\" filter by nested longname"
	@echo "                    ARGS=\"-t 'Successful*'\" filter by test glob"
	@echo "                    ARGS=\"--list\" just print discovered suites"
	@echo "                    WORKERS=N api uvicorn worker count (default 4)"
	@echo "                    POOL=N orchestrator process pool size (default 1, serial)"
	@echo "  make test-e2e-dryrun ARGS=...   parse + list without running (no listener)"

up: $(BUILD_STAMP)
	$(COMPOSE) up -d

$(BUILD_STAMP): $(BUILD_DEPS)
	$(COMPOSE) build
	@touch $@

rebuild:
	$(COMPOSE) build
	@touch $(BUILD_STAMP)
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v
	$(COMPOSE) up -d

admin:
	$(COMPOSE) exec api python scripts/create_admin.py \
	  --username admin --email admin@example.com --password admin123

backup:
	COMPOSE_FILE=docker-compose-dev.yml scripts/backup.sh

build-client: _up-api
	$(COMPOSE) exec -T -w /testjam-client api sh -c \
	  "rm -rf dist build && pip install --quiet build && python -m build"

test: test-api test-front test-e2e

_up-api: $(BUILD_STAMP)
	$(COMPOSE) up -d --wait api

_up-front: $(BUILD_STAMP)
	$(COMPOSE) up -d frontend

test-api: _up-api
	$(COMPOSE) exec -T api pytest $(ARGS)

test-client: _up-api
	$(COMPOSE) exec -T -w /testjam-client api pytest $(ARGS)

test-cli-e2e: _up-api
	-$(COMPOSE) exec -T api python scripts/create_admin.py \
	  --username admin --email admin@example.com --password admin123
	$(COMPOSE) exec -T -w /testjam-client -e TESTJAM_E2E_LIVE=1 api \
	  pytest -q tests/test_cli_e2e_smoke.py $(ARGS)

test-orchestrator:
	$(COMPOSE) --profile e2e run --rm --entrypoint "" -w /tests/e2e e2e pytest orchestrator/tests $(ARGS)

test-front: _up-front
	$(COMPOSE) exec -T frontend npm test -- --run $(ARGS)

WORKERS ?= 4
# Orchestrator pool is forced to 1 until the shared-admin e2e race is fixed
# Override with `make test-e2e POOL=N`.
POOL ?= 1
GIT_BRANCH := $(shell git symbolic-ref --short HEAD 2>/dev/null || echo HEAD)
GIT_SHA    := $(shell git rev-parse --short=7 HEAD 2>/dev/null)
GIT_VERSION := $(if $(GIT_SHA),$(GIT_BRANCH)-$(GIT_SHA))

test-e2e: export API_WORKERS = $(WORKERS)
test-e2e: export TESTJAM_VERSION = $(GIT_VERSION)
test-e2e: $(BUILD_STAMP)
	$(COMPOSE) --profile e2e build web e2e
	$(COMPOSE) up -d --wait api
	$(COMPOSE) --profile e2e run --rm -e FORCE_COLOR=1 -e ORCHESTRATOR_WORKERS=$(POOL) e2e python -m orchestrator $(ARGS)

test-e2e-dryrun:
	$(COMPOSE) --profile e2e run --rm e2e robot --dryrun $(ARGS) suites/
