COMPOSE = COMPOSE_FILE=docker-compose-dev.yml docker compose

# Rebuild trigger: image only rebuilds when one of these files changes.
# Source code is bind-mounted so day-to-day edits never need a rebuild.
BUILD_STAMP = .docker-build-stamp
BUILD_DEPS  = backend/Dockerfile backend/pyproject.toml \
              frontend/Dockerfile frontend/package.json frontend/package-lock.json

.PHONY: help up down reset rebuild admin backup test test-api test-client test-front test-e2e _up-api _up-front

help:
	@echo "Targets:"
	@echo "  make up           Start dev stack (rebuilds image only if Dockerfile/deps changed)"
	@echo "  make rebuild      Force rebuild of api + frontend images, then start"
	@echo "  make down         Stop dev stack"
	@echo "  make reset        Reset DB and restart"
	@echo "  make admin        Create admin user (admin / admin@example.com / admin123)"
	@echo "  make backup       Dump DB + uploads to ./backups (BACKUP_DIR, RETENTION_DAYS env)"
	@echo "  make test         Run backend + frontend + e2e (boots what it needs)"
	@echo "  make test-api     pytest        ARGS=path/to/test"
	@echo "  make test-client  pytest /client/tests — SDK tests run in api container"
	@echo "  make test-front   vitest        ARGS=__tests__/Foo"
	@echo "  make test-e2e     robot from suites/ root (preserves hierarchy via __init__.robot)"
	@echo "                    ARGS=\"-s '01 Auth'\" filter by leaf suite name"
	@echo "                    ARGS=\"-s '*.Api Server.01 Auth'\" mid-tree path (needs *. prefix)"
	@echo "                    ARGS=\"-t 'Successful*'\" filter by test glob"
	@echo "                    WORKERS=N api worker count (default 4)"
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

test: test-api test-front test-e2e

_up-api:
	$(COMPOSE) up -d --wait api

_up-front:
	$(COMPOSE) up -d frontend

test-api: _up-api
	$(COMPOSE) exec -T api pytest $(ARGS)

test-client: _up-api
	$(COMPOSE) exec -T -w /client api pytest $(ARGS)

test-front: _up-front
	$(COMPOSE) exec -T frontend npm test -- --run $(ARGS)

WORKERS ?= 4
test-e2e: export API_WORKERS = $(WORKERS)
test-e2e:
	$(COMPOSE) up -d --wait api
	$(COMPOSE) --profile e2e run --rm e2e robot --listener testjam_listener.TestjamListener $(ARGS) suites/

test-e2e-dryrun:
	$(COMPOSE) --profile e2e run --rm e2e robot --dryrun $(ARGS) suites/
