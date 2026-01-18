# Contributing to Mattilda Challenge

## Overview

This document provides detailed coding standards, style guidelines, and contribution workflows for the Mattilda Challenge project. For high-level architectural decisions, see the [Architecture Decision Records (ADRs)](docs/adrs/).

**Core Principle**: This project prioritizes **correctness, clarity, and maintainability** over cleverness or brevity.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style Standards](#code-style-standards)
- [Domain Invariants (Must Not Be Violated)](#domain-invariants-must-not-be-violated)
- [REST API Guidelines (Must Follow)](#rest-api-guidelines-must-follow)
- [Documentation Guidelines](#documentation-guidelines)
- [Unicode & Encoding](#unicode--encoding)
- [Testing Guidelines](#testing-guidelines)
- [Database Guidelines](#database-guidelines)
- [Observability Guidelines](#observability-guidelines)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)

---

## Development Setup

### Prerequisites

- Docker & Docker Compose

**Note**: All development happens inside Docker containers. You do not need Python or uv installed on your host machine.

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd mattilda-backend

# Start all services
make up

# Run migrations
make migrate

# Load seed data (optional)
make seed

# Access API documentation
open http://localhost:8000/docs
```

### Development Workflow

All development happens inside Docker containers:

```bash
# Open shell inside backend container
make shell

# Run tests
make test

# Run linter
make lint

# Run type checker
make typecheck

# Format code
make fmt

# Run all checks (lint + typecheck + test)
make check
```

---

## Domain Invariants (Must Not Be Violated)

The following invariants are **non-negotiable** and enforced in code review. Violations will block PRs.

See [ADR-002: Domain Model Design](docs/adrs/ADR-002-domain-model.md) for complete rationale and examples.

### Hard Invariants

| Invariant | Description | Reference |
|-----------|-------------|-----------|
| ✅ **Monetary values must be `Decimal`** | No floats, no exceptions, anywhere in domain/application | [ADR-002](docs/adrs/ADR-002-domain-model.md#1-monetary-values---decimal-arithmetic-system-wide) |
| ✅ **All domain datetimes must be UTC** | Validated via `validate_utc_timestamp()` guard | [ADR-003](docs/adrs/ADR-003-time-provider.md) |
| ✅ **Entities are immutable** | `@dataclass(frozen=True, slots=True)` with copy-on-write pattern | [ADR-001](docs/adrs/ADR-001-project-initialization.md) |
| ✅ **IDs are UUID value objects** | Never raw `UUID` in domain APIs (use `InvoiceId`, `StudentId`, etc.) | [ADR-002](docs/adrs/ADR-002-domain-model.md#2-entity-identifiers-uuid-value-objects) |
| ✅ **Payments are append-only** | No updates or deletes after creation | [ADR-002](docs/adrs/ADR-002-domain-model.md#5-payment-entity) |
| ✅ **Overdue is calculated** | Never stored as status, always computed from `due_date` and `now` | [ADR-002](docs/adrs/ADR-002-domain-model.md#4-invoice-entity) |
| ✅ **Time is injected** | Domain never calls `datetime.now()`, always parameter from `TimeProvider` | [ADR-003](docs/adrs/ADR-003-time-provider.md) |
| ✅ **`sort_by` validated in entrypoint** | Repositories trust `sort_by` is valid; validation happens in route handlers | [ADR-009](docs/adrs/ADR-009-repository-adapters.md#6-sort-validation-responsibility) |
| ✅ **Repositories never raise domain exceptions** | Return `None` for not-found; let infra errors propagate; use cases raise domain errors | [ADR-009](docs/adrs/ADR-009-repository-adapters.md#5-error-handling) |
| ✅ **Cross-aggregate filters via integration tests** | Filters spanning entities (e.g., `school_id` on invoices) must be tested with PostgreSQL | [ADR-009](docs/adrs/ADR-009-repository-adapters.md#43-cross-aggregate-filter-testing-guidelines) |

### Responsibility Boundaries

Know where logic lives to avoid architectural violations:

| Rule Type | Lives In | Example |
|-----------|----------|---------|
| Business rules | Domain entities / value objects | `Invoice.is_overdue()`, `LateFeePolicy.calculate_fee()` |
| Aggregations | Repository (database) | `balance_due`, account statement totals |
| Time access | `TimeProvider` only | `time_provider.now()` in use cases |
| Validation | `__post_init__` + guard functions | `validate_utc_timestamp()`, Decimal type checks |
| State transitions | Use cases orchestrate, entities validate | Use case updates status, entity validates transition |
| Late fees | `LateFeePolicy` value object | Formula, rounding, "original amount" rule |
| Sort field validation | Entrypoint (route handlers) | FastAPI Query enum validation, 422 on invalid `sort_by` |
| Not-found errors | Use cases | Repository returns `None`, use case raises `EntityNotFoundError` |

### Transaction Boundaries (Critical)

**Financial Use Case Transaction Rule**

Any use case that:
- Modifies financial state (invoices, payments, balances), OR
- Spans multiple repository operations

**MUST** execute inside a Unit of Work and must NOT commit outside it.

```python
# ✅ CORRECT: Use Unit of Work for multi-step financial operations
async def record_payment_use_case(
    uow: UnitOfWork,
    invoice_id: InvoiceId,
    amount: Decimal,
):
    """Record payment - requires atomic transaction."""
    async with uow:
        # Step 1: Create payment
        payment = Payment.create(...)
        await uow.payments.save(payment)
        
        # Step 2: Update invoice status
        invoice = await uow.invoices.get_by_id(invoice_id, for_update=True)
        updated_invoice = invoice.update_status(new_status, now)
        await uow.invoices.save(updated_invoice)
        
        # Step 3: Atomic commit (all or nothing)
        await uow.commit()

# ❌ Wrong: Multiple independent operations (not atomic)
async def record_payment_broken(
    invoice_repo: InvoiceRepository,
    payment_repo: PaymentRepository,
):
    payment = Payment.create(...)
    await payment_repo.save(payment)  # Separate transaction
    
    invoice = await invoice_repo.get_by_id(invoice_id)
    await invoice_repo.save(invoice)  # Separate transaction
    
    # If second save fails, payment exists but invoice unchanged!
```

**Repositories must never commit:**
- Repositories only use `session.flush()` to write to DB
- Only Unit of Work calls `session.commit()` or `session.rollback()`
- This ensures atomicity across multi-repository operations

**Enforcement:**
- Code review must verify no `commit()` calls in repository code
- Integration tests must verify rollback on exceptions
- See [ADR-004: PostgreSQL Persistence](docs/adrs/ADR-004-postgresql-persistence.md) for complete rationale

### Common Mistakes to Avoid

- ❌ Calculating late fees in controllers or repositories
- ❌ Updating invoice status in repositories (use cases do this)
- ❌ Reading `datetime.now()` directly anywhere
- ❌ Using floats for money "temporarily" (no temporary violations)
- ❌ Storing calculated fields (overdue, balance_due)
- ❌ Raising domain exceptions from repositories (return `None` instead)
- ❌ Validating `sort_by` in repositories (do it in entrypoint)
- ❌ Unit testing cross-aggregate filters with in-memory repositories

---

## REST API Guidelines (Must Follow)

The following REST layer patterns are **non-negotiable** for consistency and maintainability. Violations will be caught in code review.

See [ADR-005: REST API Design](docs/adrs/ADR-005-rest-api-design.md) for complete rationale.

### Controller Pattern: Parse → Map → Execute → Map → Return

**Rule**: Controllers orchestrate only. No business logic, no inline conversions, no try/catch blocks.

```python
# ✅ CORRECT: Thin controller following pattern
@router.post("/invoices")
async def create_invoice(
    request: InvoiceCreateRequestDTO,
    session: AsyncSession = Depends(get_session),
    time_provider: TimeProvider = Depends(get_time_provider),
) -> InvoiceResponseDTO:
    """Create invoice endpoint handler."""
    async with UnitOfWork(session) as uow:
        # 1. Parse (handled by FastAPI + Pydantic)
        
        # 2. Map DTO to domain request
        domain_request = InvoiceMapper.to_create_request(
            request,
            time_provider.now()
        )
        
        # 3. Execute use case
        use_case = CreateInvoiceUseCase()
        invoice = await use_case.execute(uow, domain_request)
        
        # 4. Map domain entity to response DTO
        return InvoiceMapper.to_response(invoice, time_provider.now())


# ❌ Wrong: Business logic in controller
@router.post("/invoices")
async def create_invoice(request: InvoiceCreateRequestDTO):
    # Inline Decimal conversion
    amount = Decimal(request.amount)  # ❌ Should be in mapper
    
    # Business logic
    if amount <= 0:  # ❌ Should be in domain
        raise HTTPException(status_code=400)
    
    # State calculations
    status = InvoiceStatus.PENDING  # ❌ Should be in domain
    
    # Direct repository access
    invoice = await invoice_repo.save(...)  # ❌ Should use UoW via use case
    
    return invoice  # ❌ Should map to DTO
```

### Error Handling: Global Handlers Only

**Rule**: Routes do NOT catch domain exceptions. Let them propagate to global exception handlers.

```python
# ✅ Correct: Let exceptions propagate
@router.post("/payments")
async def record_payment(...):
    """Record payment endpoint handler."""
    async with UnitOfWork(session) as uow:
        use_case = RecordPaymentUseCase()
        payment = await use_case.execute(uow, request)
        # If payment exceeds balance, PaymentExceedsBalanceError propagates
        # Global handler catches and returns 400
        return PaymentMapper.to_response(payment)


# ❌ Wrong: Catching domain exceptions in route
@router.post("/payments")
async def record_payment(...):
    try:
        use_case = RecordPaymentUseCase()
        payment = await use_case.execute(uow, request)
    except PaymentExceedsBalanceError as e:  # ❌ Duplicates global handler
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidPaymentAmountError as e:
        raise HTTPException(status_code=422, detail=str(e))
    # This logic should be in app.py global handlers!
```

**Global handlers are registered once in `app.py`:**

```python
@app.exception_handler(PaymentExceedsBalanceError)
async def handle_business_rule_violation(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

### Monetary Values: String Boundary Enforcement

**Rule**: All monetary values are strings in DTOs, Decimal in domain/application.

```python
# ✅ CORRECT: DTO with string amounts
class InvoiceCreateRequestDTO(BaseModel):
    amount: str = Field(
        pattern=r"^\d+\.\d{2}$",  # Regex validates format
        examples=["1500.00"]
    )

# ✅ CORRECT: Mapper converts at boundary
class InvoiceMapper:
    @staticmethod
    def to_create_request(dto: InvoiceCreateRequestDTO, now: datetime):
        return CreateInvoiceRequest(
            amount=Decimal(dto.amount),  # ✅ str → Decimal
            ...
        )
    
    @staticmethod
    def to_response(invoice: Invoice, now: datetime):
        return InvoiceResponseDTO(
            amount=str(invoice.amount),  # ✅ Decimal → str
            ...
        )


# ❌ Wrong: Numeric type in DTO
class InvoiceCreateRequestDTO(BaseModel):
    amount: float  # ❌ Float will cause precision loss


# ❌ Wrong: Inline conversion in controller
@router.post("/invoices")
async def create_invoice(request: InvoiceCreateRequestDTO):
    amount = Decimal(request.amount)  # ❌ Should be in mapper
    ...
```

### Mapper Purity: No Side Effects

**Rule**: Mappers are pure, deterministic functions. They translate types only.

```python
# ✅ CORRECT: Pure mapper
class InvoiceMapper:
    @staticmethod
    def to_create_request(dto: InvoiceCreateRequestDTO, now: datetime):
        """Pure translation function."""
        return CreateInvoiceRequest(
            student_id=StudentId.from_string(dto.student_id),
            amount=Decimal(dto.amount),
            due_date=parse_iso8601_utc(dto.due_date),
            now=now  # Only external dependency allowed
        )


# ❌ WRONG: Mapper with side effects
class InvoiceMapper:
    @staticmethod
    async def to_create_request(dto: InvoiceCreateRequestDTO):
        # Querying repository
        student = await student_repo.get_by_id(dto.student_id)  # ❌ NO!
        
        # Accessing external service
        validation_result = await external_api.validate(dto)  # ❌ NO!
        
        # Logging
        logger.info("Creating invoice")  # ❌ NO!
        
        return CreateInvoiceRequest(...)
```

**Mappers must NOT:**
- Access repositories or databases
- Call external APIs
- Perform I/O operations
- Access mutable state beyond parameters
- Log or emit events

**Only external dependency allowed:** Injected `now` parameter for timestamp conversions.

### HTTP Status Code Semantics

**Rule**: Use status codes consistently based on error type.

| Status | When to Use | Example |
|--------|-------------|---------|
| **422** | Malformed/invalid *input values* | Format error, type mismatch, negative amount, non-UTC timestamp |
| **400** | Valid input that violates *business rules* | Invalid state transition, payment exceeds balance |
| **404** | Resource does not exist | Invoice not found, student not found |
| **500** | Unexpected error (bug) | Uncaught exception, infrastructure failure |

```python
# Domain exceptions map to HTTP status codes (in app.py):

# 422 - Input validation errors
@app.exception_handler(InvalidInvoiceAmountError)
@app.exception_handler(InvalidTimestampError)
async def handle_validation_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

# 400 - Business rule violations
@app.exception_handler(PaymentExceedsBalanceError)
@app.exception_handler(InvalidStateTransitionError)
async def handle_business_rule_violation(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

### URL Versioning

**Rule**: All endpoints use `/api/v1` prefix.

```python
# ✅ CORRECT: Versioned URL
router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])


# ❌ WRONG: No version prefix
router = APIRouter(prefix="/invoices", tags=["Invoices"])
```

### ISO 8601 Timestamps with Z Suffix

**Rule**: All timestamps in responses use ISO 8601 UTC format with explicit `Z` suffix.

```python
# ✅ CORRECT: Mapper produces ISO 8601 with Z
class InvoiceMapper:
    @staticmethod
    def to_response(invoice: Invoice, now: datetime):
        return InvoiceResponseDTO(
            created_at=invoice.created_at.isoformat(),  # Produces "2024-01-15T10:30:00+00:00"
            ...
        )


# ❌ WRONG: Missing Z or non-UTC
# "2024-01-15T10:30:00" (no timezone indicator)
# "2024-01-15T10:30:00-06:00" (offset notation)
```

**Enforcement:**
- Domain ensures all datetimes are UTC via `validate_utc_timestamp()`
- Mappers use `.isoformat()` on validated UTC datetimes
- Result always includes UTC indicator

---

## Code Style Standards

### 1. File Header

Every Python file must start with:

```python
from __future__ import annotations

# Then standard library imports
# Then third-party imports
# Then local imports
```

**Why**: Enables lazy type hint evaluation and forward references (see ADR-001).

### 2. Import Organization

Follow this order (enforced by `ruff`):

```python
from __future__ import annotations

# 1. Standard library
from datetime import datetime, UTC
from decimal import Decimal
from typing import Any

# 2. Third-party libraries
from sqlalchemy import Column, Integer
from fastapi import APIRouter

# 3. Local application imports
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.application.ports import InvoiceRepository
```

### 3. Type Hints

**Rule**: All functions must have complete type hints.

```python
# ✅ Correct
def calculate_balance(invoices: list[Invoice], payments: list[Payment]) -> Decimal:
    total_invoiced = sum(inv.amount for inv in invoices)
    total_paid = sum(pay.amount for pay in payments)
    return total_invoiced - total_paid

# ❌ Wrong: Missing type hints
def calculate_balance(invoices, payments):
    return sum(inv.amount for inv in invoices) - sum(pay.amount for pay in payments)
```

**Use `X | None` instead of `Optional[X]`**:

```python
# ✅ Correct: Modern syntax
def get_student(student_id: StudentId) -> Student | None:
    ...

# ❌ Wrong: Legacy Optional
from typing import Optional

def get_student(student_id: StudentId) -> Optional[Student]:
    ...
```

**Exception**: Private helper functions may omit return type if obvious from context.

### 4. Dataclasses

**Rule**: All domain objects use `@dataclass(frozen=True, slots=True)`.

```python
from dataclasses import dataclass
from decimal import Decimal

# ✅ Correct: Immutable with slots
@dataclass(frozen=True, slots=True)
class LateFeePolicy:
    """Immutable value object for late fee calculation."""
    monthly_rate: Decimal
    
    def __post_init__(self) -> None:
        """Validate invariants at construction."""
        if self.monthly_rate < 0:
            raise ValueError("Rate cannot be negative")
        if self.monthly_rate > Decimal("1.00"):
            raise ValueError("Rate cannot exceed 100%")

# ❌ Wrong: Mutable dataclass
@dataclass
class LateFeePolicy:
    monthly_rate: Decimal
```

**Why `frozen=True`**:
- Prevents accidental mutation
- Makes objects hashable (can use in sets, as dict keys)
- Thread-safe by default

**Why `slots=True`**:
- 40-50% memory savings per instance
- 20% faster attribute access
- Prevents dynamic attribute addition (catches typos)

### 5. Copy-on-Write Pattern

Since entities are immutable, use `dataclasses.replace()` for state changes:

```python
from dataclasses import replace

# ✅ Correct: Return new instance
def mark_as_paid(self, now: datetime) -> Invoice:
    """Return new invoice with status PAID."""
    if self.status not in [InvoiceStatus.PENDING, InvoiceStatus.PARTIALLY_PAID]:
        raise InvalidStateTransition(f"Cannot mark as paid from {self.status}")
    
    return replace(self, status=InvoiceStatus.PAID, updated_at=now)

# ❌ Wrong: Attempt to mutate (will raise FrozenInstanceError)
def mark_as_paid(self) -> None:
    self.status = InvoiceStatus.PAID
```

### 6. Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `InvoiceRepository`, `SchoolEntity` |
| Functions/Methods | snake_case | `calculate_balance()`, `get_by_id()` |
| Variables | snake_case | `total_amount`, `student_id` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_INVOICE_AMOUNT`, `DEFAULT_CURRENCY` |
| Private attributes | Leading underscore | `_session`, `_cache` |
| Type variables | Single letter or PascalCase | `T`, `EntityType` |

**Special cases**:
- Repository implementations: `Postgres{Entity}Repository` (e.g., `PostgresInvoiceRepository`)
- Use cases: Verb + noun (e.g., `CreateInvoice`, `RecordPayment`)
- DTOs: `{Entity}{Purpose}DTO` (e.g., `InvoiceCreateRequestDTO`, `StudentResponseDTO`)

### 7. Explicit Over Implicit

Write code that clearly expresses intent:

```python
# ✅ Correct: Explicit comparison
if invoice.status == InvoiceStatus.PAID:
    process_paid_invoice(invoice)

# ❌ Wrong: Implicit boolean conversion
if invoice.status:  # What does this mean?
    process_paid_invoice(invoice)

# ✅ Correct: Explicit calculation
total = sum(payment.amount for payment in payments)

# ❌ Wrong: Magic method (unclear how it works)
total = sum(payments)  # Relies on __add__? __radd__?
```

### 8. Fail Fast

Validate at construction, not later:

```python
# ✅ Correct: Fail at construction
@dataclass(frozen=True, slots=True)
class LateFeePolicy:
    monthly_rate: Decimal
    
    def __post_init__(self) -> None:
        if self.monthly_rate < 0:
            raise ValueError("Rate cannot be negative")

# ❌ Wrong: Defensive validation later
@dataclass(frozen=True, slots=True)
class LateFeePolicy:
    monthly_rate: Decimal
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        if self.monthly_rate < 0:  # Too late!
            raise ValueError("Rate cannot be negative")
        return amount * self.monthly_rate
```

### 9. Domain Purity

**Critical Rule**: Domain entities never access external resources directly.

```python
# ✅ Correct: Time injected as parameter
def calculate_late_fee(self, now: datetime) -> Decimal:
    """
    Calculate late fee using policy.
    
    Args:
        now: Current timestamp (from TimeProvider)
    """
    if not self.is_overdue(now):
        return Decimal("0.00")
    return self.late_fee_policy.calculate_fee(
        original_amount=self.amount,
        due_date=self.due_date,
        now=now,
    )

# ❌ Wrong: Domain accessing clock
def calculate_late_fee(self) -> Decimal:
    now = datetime.now(UTC)  # Domain accessing external resource!
    ...

# ❌ Wrong: Domain accessing database
def get_balance_due(self) -> Decimal:
    payments = Payment.query.filter_by(invoice_id=self.id).all()  # NO!
    return self.amount - sum(p.amount for p in payments)
```

**Why**: Domain must be:
- Testable without infrastructure
- Free of external dependencies
- Pure business logic only

---

## Documentation Guidelines

### 1. Docstring Format

Use Google-style docstrings:

```python
def record_payment(
    self,
    payment_amount: Decimal,
    now: datetime,
) -> Invoice:
    """
    Record payment and return updated invoice.
    
    Validates payment amount and updates invoice status based on
    whether payment fully covers the invoice amount.
    
    Args:
        payment_amount: Amount being paid (must be positive and <= balance)
        now: Current timestamp for updated_at field
        
    Returns:
        New invoice instance with updated status and timestamp
        
    Raises:
        InvalidPaymentAmount: If amount <= 0 or exceeds balance due
        InvalidStateTransition: If invoice cannot accept payments
        
    Example:
        >>> invoice = Invoice(id=1, amount=Decimal("1000.00"), ...)
        >>> now = datetime.now(UTC)
        >>> paid_invoice = invoice.record_payment(Decimal("1000.00"), now)
        >>> assert paid_invoice.status == InvoiceStatus.PAID
    """
    ...
```

### 2. Module Docstrings

Every module should have a docstring:

```python
"""
Invoice entity and related business rules.

This module defines the Invoice entity which represents a billing invoice
issued to a student. Invoices are immutable and follow copy-on-write pattern
for state changes.
"""
from __future__ import annotations

# ... rest of module
```

### 3. Class Docstrings

Every class should explain its purpose:

```python
@dataclass(frozen=True, slots=True)
class Invoice:
    """
    Invoice entity representing a billing invoice.
    
    Immutable entity following copy-on-write pattern. All state changes
    return new instances rather than mutating self.
    
    Business rules:
    - Invoice amount must be positive
    - Status transitions follow defined state machine
    - Timestamps must be timezone-aware UTC
    - Overdue is calculated, not stored
    
    Attributes:
        id: Unique invoice identifier (UUID value object)
        student_id: Student this invoice belongs to
        amount: Invoice amount (always positive Decimal)
        status: Current payment status
        due_date: When payment is due (UTC)
        late_fee_policy: Policy for calculating late fees
        created_at: UTC timestamp when invoice was created
        updated_at: UTC timestamp of last modification
    """
    id: InvoiceId
    student_id: StudentId
    amount: Decimal
    status: InvoiceStatus
    due_date: datetime
    late_fee_policy: LateFeePolicy
    created_at: datetime
    updated_at: datetime
```

### 4. Comments

Use comments sparingly, preferring self-documenting code:

```python
# ✅ Good: Comment explains WHY, not WHAT
# Late fees apply to ORIGINAL amount, not remaining balance,
# per business rule from billing department
monthly_fee = original_amount * self.monthly_rate

# ❌ Bad: Comment repeats code
# Calculate the monthly fee
monthly_fee = original_amount * self.monthly_rate

# ✅ Good: Complex formula explained
# Pro-rated daily fee: monthly_fee / 30 (always 30 days per billing spec)
# See ADR-002 for rationale on 30-day month convention
daily_fee = monthly_fee / Decimal("30")
```

### 5. TODO Comments

Use specific format for tracking:

```python
# TODO(your-github-username): Brief description of what needs to be done
# Related issue: #123
# Deadline: 2024-02-01
def incomplete_feature():
    raise NotImplementedError("Feature not yet implemented")
```

---

## Unicode & Encoding

All documentation and source files must be saved as **UTF-8** encoding.

### Emoji Markers

This project uses emoji markers for clarity in documentation and code comments:

| Emoji | Meaning | Usage |
|-------|---------|-------|
| ✅ | Correct | Mark correct examples, valid patterns |
| ❌ | Wrong | Mark incorrect examples, anti-patterns |

### Encoding Rules

- **Do not** replace emojis with ASCII substitutes (e.g., `[x]` instead of ❌)
- **Do not** save files as Latin-1, Windows-1252, or other legacy encodings
- **Always** use UTF-8 encoding when creating or editing files

---

## Testing Guidelines

### 1. Test Structure

Tests must mirror source structure:

```
src/mattilda_challenge/domain/entities/invoice.py
tests/unit/domain/entities/test_invoice.py
```

### 2. Test Naming

```python
def test_invoice_mark_as_paid_from_pending_succeeds():
    """Test invoice can be marked as paid from pending status."""
    ...

def test_invoice_mark_as_paid_from_paid_raises_error():
    """Test invoice cannot be marked as paid if already paid."""
    ...
```

**Format**: `test_{entity}_{method}_{scenario}_{expected_result}`

### 3. Test Structure (Arrange-Act-Assert)

```python
def test_invoice_record_payment_updates_status():
    """Test recording payment updates invoice status correctly."""
    # Arrange
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    invoice = Invoice.create(
        student_id=StudentId.generate(),
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 1, tzinfo=UTC),
        late_fee_policy=LateFeePolicy.standard(),
        now=now,
    )
    payment_amount = Decimal("500.00")
    
    # Act
    # (In real code, this would be in a use case)
    updated_invoice = invoice.update_status(InvoiceStatus.PARTIALLY_PAID, now)
    
    # Assert
    assert updated_invoice.status == InvoiceStatus.PARTIALLY_PAID
    assert invoice.status == InvoiceStatus.PENDING  # Original unchanged
    assert updated_invoice is not invoice  # Different instance
```

### 4. Test Data

**Use explicit values, not randomization**:

```python
# ✅ Correct: Explicit, reproducible
invoice = Invoice.create(
    student_id=StudentId.from_string("550e8400-e29b-41d4-a716-446655440000"),
    amount=Decimal("1500.00"),
    due_date=datetime(2024, 2, 1, tzinfo=UTC),
    ...
)

# ❌ Wrong: Random data (non-deterministic)
invoice = Invoice.create(
    student_id=StudentId.generate(),  # Random UUID each run
    amount=Decimal(str(random.uniform(100, 10000))),  # Random amount
    ...
)
```

### 5. Fixtures

Use pytest fixtures for common setup:

```python
import pytest
from datetime import datetime, UTC

@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

@pytest.fixture
def time_provider(fixed_time: datetime) -> FixedTimeProvider:
    """Provide fixed time provider for testing."""
    return FixedTimeProvider(fixed_time)

@pytest.fixture
def sample_invoice(fixed_time: datetime) -> Invoice:
    """Provide sample invoice for testing."""
    return Invoice.create(
        student_id=StudentId.from_string("550e8400-e29b-41d4-a716-446655440000"),
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 1, tzinfo=UTC),
        late_fee_policy=LateFeePolicy.standard(),
        now=fixed_time,
    )

def test_invoice_with_fixture(sample_invoice: Invoice, fixed_time: datetime):
    """Test using fixtures."""
    updated = sample_invoice.mark_as_paid(fixed_time)
    assert updated.status == InvoiceStatus.PAID
```

### 6. Testing Immutability

Always verify original is unchanged:

```python
def test_invoice_immutability():
    """Test invoice copy-on-write preserves original."""
    now = datetime(2024, 1, 1, tzinfo=UTC)
    original = Invoice.create(
        student_id=StudentId.generate(),
        amount=Decimal("1000.00"),
        ...
        now=now,
    )
    modified = original.mark_as_paid(now)
    
    # Verify original unchanged
    assert original.status == InvoiceStatus.PENDING
    
    # Verify modified has changes
    assert modified.status == InvoiceStatus.PAID
    
    # Verify different instances
    assert original is not modified
```

### 7. Testing Time-Based Scenarios

Use `FixedTimeProvider` with explicit `set_time()` calls:

```python
def test_late_fee_15_days_overdue(time_provider: FixedTimeProvider):
    """Test late fee calculation 15 days after due date."""
    invoice = Invoice.create(
        amount=Decimal("1500.00"),
        due_date=datetime(2024, 1, 1, tzinfo=UTC),
        late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
        now=datetime(2023, 12, 1, tzinfo=UTC),
    )
    
    # Set time to 15 days after due date
    time_provider.set_time(datetime(2024, 1, 16, tzinfo=UTC))
    
    fee = invoice.calculate_late_fee(time_provider.now())
    
    # Monthly fee: 1500 × 0.05 = 75.00
    # Daily fee: 75.00 / 30 = 2.50
    # 15 days × 2.50 = 37.50
    assert fee == Decimal("37.50")  # Exact equality
```

### 8. Exception Testing

```python
def test_invoice_mark_as_paid_from_paid_raises():
    """Test cannot mark paid invoice as paid again."""
    now = datetime(2024, 1, 1, tzinfo=UTC)
    invoice = Invoice.create(..., now=now)
    paid_invoice = invoice.mark_as_paid(now)
    
    with pytest.raises(InvalidStateTransition) as exc_info:
        paid_invoice.mark_as_paid(now)
    
    assert "Cannot mark as paid from status: paid" in str(exc_info.value)
```

### 9. Repository Testing Guidelines

**INVARIANT**: Cross-aggregate filters must be tested via integration tests only.

See [ADR-009: Repository Adapters](docs/adrs/ADR-009-repository-adapters.md#43-cross-aggregate-filter-testing-guidelines) for complete rationale.

| Filter Type | Unit Test (In-Memory) | Integration Test (PostgreSQL) |
|-------------|----------------------|------------------------------|
| Same-entity filters (`student_id`, `status`) | ✅ Test thoroughly | ✅ Verify query correctness |
| Cross-aggregate filters (`school_id` on invoices) | ❌ Skip or mock | ✅ **Required** |
| Date range filters | ✅ Test boundary conditions | ✅ Verify SQL behavior |

```python
# ✅ CORRECT: Unit test for same-entity filter
async def test_find_invoices_by_student_id(memory_invoice_repo):
    """Unit test - student_id is on Invoice entity."""
    invoice = create_test_invoice(student_id=StudentId(uuid4()))
    await memory_invoice_repo.save(invoice)
    
    page = await memory_invoice_repo.find(
        filters=InvoiceFilters(student_id=invoice.student_id.value),
        pagination=PaginationParams(offset=0, limit=10),
        sort=SortParams(sort_by="created_at", sort_order="desc"),
    )
    
    assert len(page.items) == 1


# ✅ CORRECT: Integration test for cross-aggregate filter
@pytest.mark.integration
async def test_find_invoices_by_school_id(postgres_session):
    """Integration test - school_id requires join through Student."""
    # Setup: create school, student, invoice in database
    school = await create_school_in_db(postgres_session)
    student = await create_student_in_db(postgres_session, school_id=school.id)
    invoice = await create_invoice_in_db(postgres_session, student_id=student.id)
    
    repo = PostgresInvoiceRepository(postgres_session)
    page = await repo.find(
        filters=InvoiceFilters(school_id=school.id.value),
        pagination=PaginationParams(offset=0, limit=10),
        sort=SortParams(sort_by="created_at", sort_order="desc"),
    )
    
    assert len(page.items) == 1
    assert page.items[0].id == invoice.id


# ❌ WRONG: Unit test for cross-aggregate filter
async def test_find_invoices_by_school_id_unit(memory_invoice_repo):
    """Don't do this - in-memory can't simulate cross-aggregate joins."""
    # This test would give false confidence - the filter is silently ignored!
```

---

## Database Guidelines

### Index Justification Requirement

**Any new database index must be documented with:**

1. **The query pattern it supports**
   - Which API endpoint or use case requires it
   - Example SQL query that benefits from the index

2. **Why simpler alternatives are insufficient**
   - For composite indexes: why single-column indexes don't work
   - For single-column indexes: why no index causes problems

3. **What other candidate indexes were considered and rejected**
   - Explain trade-offs (e.g., write overhead vs read improvement)

**Example (correct documentation):**

```python
# infrastructure/postgres/models/invoice_model.py

__table_args__ = (
    # Composite index: (student_id, status)
    # Query: "Get pending invoices for student X" (account statement use case)
    # Why: Single index on student_id requires filtering status in application (slower)
    # Rejected: Index on status only (would scan all pending invoices, filter by student)
    # Performance: 100x faster than single-column index for this query
    Index("ix_invoices_student_status", "student_id", "status"),
    
    # Single index: status
    # Query: "Get all pending invoices" (admin dashboard)
    # Why: Composite (student_id, status) cannot be used for status-only queries
    Index("ix_invoices_status", "status"),
)
```

**Anti-pattern (insufficient documentation):**

```python
# ❌ Wrong: No justification
Index("ix_invoices_amount", "amount"),  # Why? What query needs this?
```

**Prevention of index sprawl:**
- Indexes add ~10-20% storage overhead per index
- Indexes slow down INSERT/UPDATE operations
- Unused indexes waste resources
- Use `pg_stat_user_indexes` to monitor index usage
- Remove indexes with `idx_scan = 0` after observation period

See [ADR-004: Database Index Strategy](docs/adrs/ADR-004-postgresql-persistence.md#9-database-index-strategy) for detailed guidelines.

---

## Observability Guidelines

See [ADR-008: Observability Strategy](docs/adrs/ADR-008-observability.md) for complete implementation details.

### Structured Logging

**Rules for logging:**

```python
import structlog

logger = structlog.get_logger()

# ✅ Correct: Structured fields, no PII
logger.info(
    "invoice_created",
    invoice_id=str(invoice.id),
    student_id=str(invoice.student_id),
    amount=str(invoice.amount),  # Decimal as string
)

# ❌ Wrong: Unstructured message
logger.info(f"Created invoice {invoice.id} for student {invoice.student_id}")

# ❌ Wrong: Logging PII
logger.info("invoice_created", email=student.email, name=student.name)

# ❌ Wrong: Logging request/response bodies
logger.info("request_received", body=request.json())
```

**What to log:**

| Event | Level | Fields |
|-------|-------|--------|
| Invoice created | INFO | `invoice_id`, `student_id`, `amount` |
| Payment recorded | INFO | `payment_id`, `invoice_id`, `amount` |
| State transition | INFO | `invoice_id`, `from_status`, `to_status` |
| Cache hit | DEBUG | `key` |
| Cache miss | DEBUG | `key` |
| Validation error | WARNING | `field`, `error` |
| Database error | ERROR | `operation`, `error` |

**What NOT to log:**
- Request/response bodies (size concerns, potential PII)
- Personally Identifiable Information (emails, names, addresses)
- Raw SQL queries with parameter values
- Secrets, tokens, or credentials

### Request ID Propagation

All logs automatically include `request_id` via middleware:

```python
# Middleware sets request_id in contextvars
# structlog processor adds it to every log entry

{"timestamp": "...", "level": "info", "message": "invoice_created", 
 "request_id": "abc-123-def", "invoice_id": "..."}
```

### Health Checks

**Pattern for dependency checks:**

```python
async def check_database_health(session: AsyncSession) -> DependencyStatus:
    """Check database connectivity."""
    try:
        await session.execute(text("SELECT 1"))
        return DependencyStatus(name="database", status="healthy")
    except Exception as e:
        return DependencyStatus(
            name="database", 
            status="unhealthy", 
            error=str(e)
        )
```

---

## Git Workflow

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/{description}` | `feature/add-payment-entity` |
| Bug fix | `fix/{description}` | `fix/invoice-calculation-error` |
| ADR | `adr/{number}-{description}` | `adr/002-domain-model` |
| Refactor | `refactor/{description}` | `refactor/extract-late-fee-policy` |

### Commit Messages

Follow conventional commits:

```
type(scope): brief description

Longer explanation if needed. Wrap at 72 characters.

- Bullet points for multiple changes
- Reference issues: Fixes #123

Breaking changes start with BREAKING CHANGE:
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Changes to build process or auxiliary tools

**Examples**:

```
feat(domain): add LateFeePolicy value object

Implements immutable LateFeePolicy following ADR-002 standards.
Encapsulates late fee calculation formula and business rules.

- Add LateFeePolicy dataclass with frozen=True, slots=True
- Implement calculate_fee() method with pro-rated daily fees
- Add comprehensive unit tests for boundary conditions

Fixes #45
```

```
fix(repository): correct Decimal conversion in invoice mapper

Invoice amounts were being converted to float in PostgresInvoiceRepository,
causing precision loss. Now properly converts to Decimal from NUMERIC column.

BREAKING CHANGE: InvoiceModel.amount now returns Decimal, not float
```

---

## PR Requirements for Domain Changes

If your PR touches any of the following, additional requirements apply:

**Domain-critical code**:
- `Invoice`, `Payment`, `Student`, `School` entities
- `LateFeePolicy` or any value objects
- Monetary calculations (anywhere)
- Time logic or `TimeProvider`
- Repository implementations

**Required in PR**:

### 1. Tests Must Assert Exact Equality

```python
# ✅ Correct - exact Decimal equality
assert late_fee == Decimal("37.50")
assert balance == Decimal("1500.00")

# ❌ Wrong - approximate equality not allowed for money
assert late_fee == pytest.approx(37.50)
```

### 2. Tests Must Cover UTC Rejection

```python
# ✅ Correct - test that naive/non-UTC datetimes are rejected
def test_invoice_rejects_naive_datetime():
    naive = datetime(2024, 1, 1, 12, 0, 0)  # No timezone
    
    with pytest.raises(InvalidInvoiceDataError) as exc:
        Invoice.create(..., due_date=naive, now=datetime.now(UTC))
    
    assert "must have UTC timezone" in str(exc.value)
```

### 3. Explicit Rounding Assertions

```python
# ✅ Correct - document rounding behavior
def test_late_fee_rounds_half_up():
    """Test that 2.5 cents rounds up to 3 cents (ROUND_HALF_UP)."""
    policy = LateFeePolicy(monthly_rate=Decimal("0.05"))
    
    # Engineered to produce 2.5 cents after calculation
    fee = policy.calculate_fee(...)
    
    assert fee == Decimal("0.03")  # 2.5 → 3 (up)
```

### 4. No New Floats Crossing Boundaries

```python
# ✅ Correct - convert at boundary
class InvoiceMapper:
    @staticmethod
    def to_create_request(dto: InvoiceCreateRequestDTO, now: datetime):
        return CreateInvoiceRequest(
            amount=Decimal(dto.amount),  # Convert immediately
            ...
        )

# ❌ Wrong - float enters domain
async def create_invoice(request: CreateInvoiceRequest):
    invoice = Invoice.create(amount=request.amount)  # float!
```

### 5. Immutability Verification

```python
# ✅ Correct - verify copy-on-write preserves original
def test_invoice_mark_as_paid_immutability():
    now = datetime(2024, 1, 1, tzinfo=UTC)
    original = Invoice.create(..., now=now)
    updated = original.update_status(InvoiceStatus.PAID, now)
    
    assert original.status == InvoiceStatus.PENDING  # Unchanged
    assert updated.status == InvoiceStatus.PAID
    assert original is not updated  # Different objects
```

**Reviewers will check for**:
- All monetary assertions use exact `Decimal` equality
- UTC validation is tested (rejection of naive/non-UTC)
- Rounding behavior is documented and tested
- No floats in domain/application layers
- Original entities unchanged after copy-on-write operations

---

## Pull Request Process

### Before Creating PR

1. **Run checks locally**:
   ```bash
   make check  # Runs lint + typecheck + test
   ```

2. **Update documentation**:
   - Add/update docstrings
   - Update README if needed
   - Create/update ADR if architectural decision

3. **Add tests**:
   - Unit tests for domain logic (required)
   - Integration tests if touching infrastructure

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Code follows style guidelines (ruff passes)
- [ ] Type hints complete (mypy passes)
- [ ] Tests added/updated (pytest passes)
- [ ] Documentation updated
- [ ] ADR created/updated if needed
- [ ] Self-review completed

## Testing
How was this tested?

## Related Issues
Fixes #(issue number)
```

### Review Criteria

Reviewers will check:

1. **Correctness**: Does it solve the problem?
2. **Architecture**: Follows Clean Architecture and ADRs?
3. **Immutability**: Uses frozen dataclasses and copy-on-write?
4. **Domain purity**: Domain doesn't access external resources?
5. **Domain invariants**: No violations of hard invariants (see [Domain Invariants](#domain-invariants-must-not-be-violated))?
6. **Type safety**: Complete type hints, mypy passes?
7. **Tests**: Adequate coverage, testing immutability and invariants?
8. **Documentation**: Clear docstrings, ADR if needed?
9. **Simplicity**: Is it as simple as possible?

**For domain changes**: See [PR Requirements for Domain Changes](#pr-requirements-for-domain-changes) for additional criteria.
