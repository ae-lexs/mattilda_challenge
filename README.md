# Mattilda Challenge

A production-grade school billing system demonstrating **Clean Architecture**, **domain-driven design**, and **financial correctness**.

## What This Project Demonstrates

- **Clean Architecture** with strict dependency rules (domain → application → infrastructure)
- **Financial precision** using `Decimal` arithmetic (never floats)
- **Immutable domain model** with copy-on-write pattern
- **Explicit time injection** for deterministic behavior
- **Comprehensive testing** (unit + integration)
- **Production-ready observability** (structured logging, metrics, health checks)

## Quick Start

```bash
# Start all services (PostgreSQL, Redis, API) & Database migrations run automatically
make up

# Seed sample data (idempotent)
make seed

# Open API documentation
open http://0.0.0.0:8000/redoc
```

## API Documentation

Once running, explore the API at:

| URL | Description |
|-----|-------------|
| http://0.0.0.0/:8000/docs | Swagger UI (interactive) |
| http://0.0.0.0:8000/redoc | ReDoc (readable) |
| http://0.0.0.0:8000/health | Health check |
| http://0.0.0.0:8000/metrics | Prometheus metrics |

### Key Endpoints

| Resource | Endpoints |
|----------|-----------|
| Schools | `GET/POST /api/v1/schools`, `GET/PUT/DELETE /api/v1/schools/{id}`, `GET /api/v1/schools/{id}/account-statement` |
| Students | `GET/POST /api/v1/students`, `GET/PUT/DELETE /api/v1/students/{id}`, `GET /api/v1/students/{id}/account-statement` |
| Invoices | `GET/POST /api/v1/invoices`, `GET/PUT/DELETE /api/v1/invoices/{id}`, `POST /api/v1/invoices/{id}/cancel` |
| Payments | `GET/POST /api/v1/payments`, `GET /api/v1/payments/{id}` |

## Essential Commands

```bash
# Development
make up                  # Start services
make down                # Stop services
make logs                # View logs

# Database
make migrate             # Run migrations
make seed                # Load sample data

# Testing
make test                # Run unit tests
make test-integration    # Run integration tests (requires DB)
make test-all            # Run all tests

# Code Quality
make check               # Run lint + typecheck + test
make lint                # Ruff linting
make typecheck           # Mypy strict mode
```

See `make help` for all available commands.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.14 |
| Framework | FastAPI |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Logging | structlog |
| Metrics | prometheus-fastapi-instrumentator |
| Testing | pytest |
| Linting | ruff, mypy (strict) |
| Dependencies | uv |

## Architecture Decision Records

All architectural decisions are documented in ADRs:

| ADR | Title |
|-----|-------|
| [ADR-001](docs/ADR-001.md) | Project Initialization & Structure |
| [ADR-002](docs/ADR-002.md) | Domain Model Design |
| [ADR-003](docs/ADR-003.md) | Time Provider Interface |
| [ADR-004](docs/ADR-004.md) | PostgreSQL Persistence |
| [ADR-005](docs/ADR-005.md) | REST API Design |
| [ADR-006](docs/ADR-006.md) | Redis Caching Strategy |
| [ADR-007](docs/ADR-007.md) | Pagination Strategy |
| [ADR-008](docs/ADR-008.md) | Observability Strategy |
| [ADR-009](docs/ADR-009.md) | Repository Pattern |
| [ADR-010](docs/ADR-010.md) | UseCase Pattern & Error Handling |

## Project Structure

```
src/mattilda_challenge/
├── domain/           # Entities, value objects, exceptions (zero dependencies)
├── application/      # Use cases, ports (interfaces), DTOs
├── infrastructure/   # PostgreSQL, Redis, adapters (implements ports)
└── entrypoints/      # FastAPI routes, HTTP DTOs, mappers
```

For detailed structure, see [ADR-001](docs/ADR-001.md).

## Core Design Principles

| Principle | Implementation |
|-----------|----------------|
| Monetary precision | All money uses `Decimal`, never `float` |
| Time injection | Domain never calls `datetime.now()` directly |
| Immutability | Entities use `frozen=True` dataclasses |
| Ports & Adapters | All I/O behind abstract interfaces |
| Unit of Work | Atomic transactions across repositories |

For details, see [ADR-002](docs/ADR-002.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Testing

```bash
make test              # Unit tests (no DB required)
make test-integration  # Integration tests
make test-coverage     # Coverage report
```

Tests use in-memory adapters for isolation. See [CONTRIBUTING.md](CONTRIBUTING.md#testing-guidelines).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Coding standards and invariants
- Testing guidelines
- Domain rules that must not be violated

## License

MIT License
