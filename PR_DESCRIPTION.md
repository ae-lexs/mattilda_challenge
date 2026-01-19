# Implement ADR-005: REST API Design with FastAPI

## Description

This PR implements the complete REST API layer for the Mattilda Challenge school billing system, following the design specified in ADR-005. It also completes the implementation of ADR-008 (Observability) and marks all 10 ADRs as fully implemented.

### What's Included

**REST API Endpoints:**
- Schools: CRUD + account statement (`/api/v1/schools`)
- Students: CRUD + account statement (`/api/v1/students`)
- Invoices: CRUD + cancel endpoint (`/api/v1/invoices`)
- Payments: List, create, get (`/api/v1/payments`)
- Health: `/health`, `/health/live`, `/health/ready`
- Metrics: `/metrics` (Prometheus format)

**HTTP Layer Components:**
- Request/Response DTOs with Pydantic validation
- Mappers for DTO ↔ domain entity conversion
- Global exception handlers (404, 400, 422, 500)
- Dependency injection for UoW, TimeProvider, Cache, Redis, Session

**Observability (ADR-008):**
- Structured logging with `structlog` (JSON in prod, colored console in dev)
- Request ID middleware with `X-Request-ID` header propagation
- Prometheus metrics via `prometheus-fastapi-instrumentator`
- Health checks with dependency status (DB, Redis latency)

**Developer Experience:**
- Idempotent database seed script (`make seed`)
- Comprehensive unit tests for DTOs, mappers, and routes
- Simplified README for challenge reviewers

## Type of Change
- [x] New feature
- [x] Documentation update

## Checklist
- [x] Code follows style guidelines (ruff passes)
- [x] Type hints complete (mypy passes)
- [x] Tests added/updated (pytest passes)
- [x] Documentation updated
- [x] ADR created/updated if needed
- [x] Self-review completed

## Testing

### Unit Tests Added
```
tests/unit/entrypoints/http/
├── conftest.py                    # Shared fixtures
├── dtos/
│   ├── test_invoice_dtos.py       # Invoice DTO validation
│   ├── test_payment_dtos.py       # Payment DTO validation
│   ├── test_school_dtos.py        # School DTO validation
│   └── test_student_dtos.py       # Student DTO validation
├── mappers/
│   ├── test_invoice_mapper.py     # Invoice mapping tests
│   ├── test_payment_mapper.py     # Payment mapping tests
│   ├── test_school_mapper.py      # School mapping tests
│   └── test_student_mapper.py     # Student mapping tests
└── routes/
    ├── test_health.py             # Health endpoint tests
    ├── test_invoices.py           # Invoice route tests
    ├── test_payments.py           # Payment route tests
    ├── test_schools.py            # School route tests
    └── test_students.py           # Student route tests
```

### How to Test

```bash
# Run unit tests
make test

# Run all tests (unit + integration)
make test-all

# Run code quality checks
make check

# Manual API testing
make up
make seed
open http://0.0.0.0:8000/redoc
```

### API Verification

Once running, verify key endpoints:

```bash
# Health check
curl http://0.0.0.0:8000/health

# List schools (seeded data)
curl http://0.0.0.0:8000/api/v1/schools

# Get school account statement
curl http://0.0.0.0:8000/api/v1/schools/{school_id}/account-statement

# Prometheus metrics
curl http://0.0.0.0:8000/metrics
```

## Files Changed

| Category | Files |
|----------|-------|
| HTTP DTOs | `entrypoints/http/dtos/*.py` (7 files) |
| HTTP Mappers | `entrypoints/http/mappers/*.py` (5 files) |
| HTTP Routes | `entrypoints/http/routes/*.py` (5 files) |
| App & Dependencies | `entrypoints/http/app.py`, `dependencies.py` |
| Observability | `infrastructure/observability/*.py` (3 files) |
| Tests | `tests/unit/entrypoints/http/**/*.py` (14 files) |
| Seed Script | `scripts/seed_database.py` |
| Config | `Dockerfile`, `Makefile`, `pyproject.toml` |
| Docs | `README.md`, `ADR-005.md`, `ADR-008.md`, `ADR-010.md` |

## ADR Implementation Status

All 10 ADRs are now marked as **Implemented**:

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Project Initialization & Structure | ✅ |
| ADR-002 | Domain Model Design | ✅ |
| ADR-003 | Time Provider Interface | ✅ |
| ADR-004 | PostgreSQL Persistence | ✅ |
| ADR-005 | REST API Design | ✅ |
| ADR-006 | Redis Caching Strategy | ✅ |
| ADR-007 | Pagination Strategy | ✅ |
| ADR-008 | Observability Strategy | ✅ |
| ADR-009 | Repository Pattern | ✅ |
| ADR-010 | UseCase Pattern & Error Handling | ✅ |
