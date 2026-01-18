SHELL := /bin/sh

.PHONY: help up down logs ps sh lock sync test test-unit test-integration test-all test-file test-coverage lint lint-fix typecheck fmt check migrate migrate-new

help:
	@echo "mattilda-challenge commands:"
	@echo ""
	@echo "Docker:"
	@echo "  make up             Start services (foreground)"
	@echo "  make down           Stop services and remove volumes"
	@echo "  make logs           Tail service logs"
	@echo "  make ps             Show running containers"
	@echo "  make sh             Shell inside api container"
	@echo ""
	@echo "Dependencies:"
	@echo "  make lock           Generate/update uv.lock"
	@echo "  make sync           Install deps from lock (frozen)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run unit tests (default, no DB required)"
	@echo "  make test-unit      Run unit tests only (alias for test)"
	@echo "  make test-integration  Run integration tests (requires DB)"
	@echo "  make test-all       Run all tests (unit + integration)"
	@echo "  make test-file FILE=path  Run specific test file"
	@echo "  make test-coverage  Run tests with coverage report (unit only)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Ruff check"
	@echo "  make lint-fix       Ruff check and fix"
	@echo "  make fmt            Ruff format"
	@echo "  make typecheck      Mypy strict typecheck"
	@echo "  make check          Run lint + typecheck + test"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run pending migrations"
	@echo "  make migrate-new MSG=desc  Create new migration"


up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

sh:
	docker compose run --rm api sh

lock:
	docker compose run --rm api uv lock

sync:
	docker compose run --rm api uv sync --frozen

test:
	docker compose run --rm api uv run pytest

test-unit: test

test-integration:
	docker compose run --rm api uv run pytest -m integration

test-all:
	docker compose run --rm api uv run pytest -m ""

test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required. Usage: make test-file FILE=path/to/test.py"; \
		exit 1; \
	fi
	docker compose run --rm api uv run pytest $(FILE) -v

test-coverage:
	docker compose run --rm api uv run pytest --cov=src/mattilda_challenge --cov-report=term-missing

lint:
	docker compose run --rm api uv run ruff check .

lint-fix:
	docker compose run --rm api uv run ruff check --fix .

fmt:
	docker compose run --rm api uv run ruff format .

typecheck:
	docker compose run --rm api uv run mypy src

check: lint typecheck test

migrate:
	docker compose run --rm api uv run alembic upgrade head

migrate-new:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG parameter required. Usage: make migrate-new MSG=\"description\""; \
		exit 1; \
	fi
	docker compose run --rm api uv run alembic revision --autogenerate -m "$(MSG)"
