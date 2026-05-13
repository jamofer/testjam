COMPOSE = COMPOSE_FILE=docker-compose-dev.yml docker compose

.PHONY: help up down reset admin backup test test-api test-front test-e2e _up-api _up-front

help:
	@echo "Targets:"
	@echo "  make up           Start dev stack (db, api, frontend, mailpit)"
	@echo "  make down         Stop dev stack"
	@echo "  make reset        Reset DB and restart"
	@echo "  make admin        Create admin user (admin / admin@example.com / admin123)"
	@echo "  make backup       Dump DB + uploads to ./backups (BACKUP_DIR, RETENTION_DAYS env)"
	@echo "  make test         Run backend + frontend + e2e (boots what it needs)"
	@echo "  make test-api     pytest        ARGS=path/to/test"
	@echo "  make test-front   vitest        ARGS=__tests__/Foo"
	@echo "  make test-e2e     robot         ARGS=suites/01_auth.robot"

up:
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

test-front: _up-front
	$(COMPOSE) exec -T frontend npm test -- --run $(ARGS)

test-e2e:
	$(COMPOSE) --profile e2e run --rm e2e robot --listener testjam_listener.TestjamListener $(if $(ARGS),$(ARGS),suites/)
