# Canonical developer commands (LOCAL-DEVELOPMENT.md).
# README and CI use this interface and no other.

COMPOSE := docker compose -f infrastructure/control-plane/compose.yaml

.PHONY: help bootstrap check test test-contract test-contract-ts test-contract-py \
        stack-up stack-down stack-ps db-migrate db-status db-reset test-integration

help:
	@echo "bootstrap         install toolchains and dependencies"
	@echo "stack-up          start postgres, redis, storage and mail"
	@echo "stack-down        stop the local stack (keeps volumes)"
	@echo "stack-ps          show local stack status"
	@echo "db-migrate        apply pending migrations"
	@echo "db-status         show applied and pending migrations"
	@echo "db-reset          drop and recreate the control database"
	@echo "check             format, lint and type checks"
	@echo "test              all tests"
	@echo "test-contract     shared contract tests in both ecosystems"
	@echo "test-integration  database, policy and isolation tests"
	@echo "test-api          domain API tests"
	@echo "api-dev           run the domain API on :8000"

bootstrap:
	pnpm install
	cd packages/contracts/python && uv sync
	cd apps/domain-api && uv sync

check:
	@echo "no checks wired yet"

test: test-contract test-integration test-api

stack-up:
	$(COMPOSE) up -d
	@echo "postgres 55432 | redis 56379 | storage 59000 (console 59001) | mail 58125"

stack-down:
	$(COMPOSE) down

stack-ps:
	$(COMPOSE) ps

db-migrate:
	python scripts/db.py migrate

db-status:
	python scripts/db.py status

db-reset:
	python scripts/db.py reset
	python scripts/db.py migrate

# Proves tenant isolation as the API's own database role (I0-05). Requires the
# stack to be up and migrated.
test-integration:
	python -m unittest discover -s tests/integration -v

test-api:
	cd apps/domain-api && .venv/Scripts/python.exe -m unittest discover -s tests

api-dev:
	cd apps/domain-api && .venv/Scripts/python.exe -m uvicorn aione_domain.main:app --reload --port 8000

# Both suites read the same fixtures. Passing here and there is what proves the
# TypeScript and Python canonicalizers agree byte for byte (ADR-015).
test-contract: test-contract-ts test-contract-py

test-contract-ts:
	node --test packages/contracts/ts/test/*.test.ts

test-contract-py:
	cd packages/contracts/python && PYTHONPATH=. python -m unittest discover -s tests
