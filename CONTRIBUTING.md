# Contributing to Mattilda Challenge

## Overview

This document provides detailed coding standards, style guidelines, and contribution workflows for the Mattilda Challenge project. For high-level architectural decisions, see the [Architecture Decision Records (ADRs)](docs/adrs/).

**Core Principle**: This project prioritizes **correctness, clarity, and maintainability** over cleverness or brevity.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style Standards](#code-style-standards)
- [Documentation Guidelines](#documentation-guidelines)
- [Testing Guidelines](#testing-guidelines)
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
```

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
from datetime import datetime
from decimal import Decimal
from typing import Any

# 2. Third-party libraries
from sqlalchemy import Column, Integer
from fastapi import APIRouter

# 3. Local application imports
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.ports import InvoiceRepository
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
def get_student(student_id: int) -> Student | None:
    ...

# ❌ Wrong: Legacy Optional
from typing import Optional

def get_student(student_id: int) -> Optional[Student]:
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
class Money:
    """Immutable value object for monetary amounts."""
    amount: Decimal
    currency: str = "MXN"
    
    def __post_init__(self) -> None:
        """Validate invariants at construction."""
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")

# ❌ Wrong: Mutable dataclass
@dataclass
class Money:
    amount: Decimal
    currency: str = "MXN"
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
class Money:
    amount: Decimal
    
    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

# ❌ Wrong: Defensive validation later
@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    
    def add(self, other: Money) -> Money:
        if self.amount < 0 or other.amount < 0:  # Too late!
            raise ValueError("Negative amounts not allowed")
        return Money(self.amount + other.amount)
```

### 9. No Magic

Avoid hidden behavior:

```python
# ✅ Correct: Explicit factory method
@classmethod
def create(
    cls,
    student_id: int,
    amount: Decimal,
    due_date: datetime,
    now: datetime,
) -> Invoice:
    """
    Create new invoice with validation.
    
    Generates invoice number and sets initial status.
    """
    invoice_number = generate_invoice_number()
    return cls(
        id=0,  # Will be set by repository
        student_id=student_id,
        invoice_number=invoice_number,
        amount=amount,
        due_date=due_date,
        status=InvoiceStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

# ❌ Wrong: Magic __init__ with side effects
def __init__(self, student_id: int, amount: Decimal, due_date: datetime):
    self.invoice_number = generate_invoice_number()  # Hidden!
    self.status = InvoiceStatus.PENDING  # Hidden!
```

### 10. Domain Purity

**Critical Rule**: Domain entities never access external resources directly.

```python
# ✅ Correct: Time injected as parameter
def record_payment(self, amount: Decimal, now: datetime) -> Invoice:
    """
    Record payment and update status.
    
    Args:
        amount: Payment amount
        now: Current timestamp (from TimeProvider)
    """
    new_status = self._calculate_status(amount)
    return replace(self, status=new_status, updated_at=now)

# ❌ Wrong: Domain accessing clock
def record_payment(self, amount: Decimal) -> Invoice:
    new_status = self._calculate_status(amount)
    return replace(
        self,
        status=new_status,
        updated_at=datetime.now(UTC)  # Domain accessing external resource!
    )

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
    
    Attributes:
        id: Unique invoice identifier
        student_id: Student this invoice belongs to
        amount: Invoice amount (always positive)
        status: Current payment status
        created_at: UTC timestamp when invoice was created
        updated_at: UTC timestamp of last modification
    """
    id: int
    student_id: int
    amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime
```

### 4. Comments

Use comments sparingly, preferring self-documenting code:

```python
# ✅ Good: Comment explains WHY, not WHAT
# Use database transaction time (not system time) to avoid clock skew
# across multiple application instances
now = self.time_provider.now()

# ❌ Bad: Comment repeats code
# Set status to paid
invoice.status = InvoiceStatus.PAID

# ✅ Good: Complex algorithm explained
# Knuth-Morris-Pratt algorithm for O(n) string matching
# See: https://en.wikipedia.org/wiki/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm
pattern_index = self._kmp_search(text, pattern)
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
    invoice = Invoice(
        id=1,
        student_id=1,
        amount=Decimal("1000.00"),
        status=InvoiceStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    payment_amount = Decimal("500.00")
    
    # Act
    updated_invoice = invoice.record_payment(payment_amount, now)
    
    # Assert
    assert updated_invoice.status == InvoiceStatus.PARTIALLY_PAID
    assert invoice.status == InvoiceStatus.PENDING  # Original unchanged
    assert updated_invoice is not invoice  # Different instance
```

### 4. Test Data

**Use explicit values, not randomization**:

```python
# ✅ Correct: Explicit, reproducible
invoice = Invoice(
    id=1,
    student_id=42,
    amount=Decimal("1500.00"),
    ...
)

# ❌ Wrong: Random data (non-deterministic)
invoice = Invoice(
    id=random.randint(1, 1000),
    student_id=random.randint(1, 100),
    amount=Decimal(str(random.uniform(100, 10000))),
    ...
)
```

### 5. Fixtures

Use pytest fixtures for common setup:

```python
import pytest
from datetime import datetime, UTC

@pytest.fixture
def fixed_time():
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

@pytest.fixture
def sample_invoice(fixed_time):
    """Provide sample invoice for testing."""
    return Invoice(
        id=1,
        student_id=1,
        amount=Decimal("1000.00"),
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )

def test_invoice_with_fixture(sample_invoice, fixed_time):
    """Test using fixtures."""
    updated = sample_invoice.mark_as_paid(fixed_time)
    assert updated.status == InvoiceStatus.PAID
```

### 6. Testing Immutability

Always verify original is unchanged:

```python
def test_invoice_immutability():
    """Test invoice copy-on-write preserves original."""
    original = Invoice(...)
    modified = original.mark_as_paid(now)
    
    # Verify original unchanged
    assert original.status == InvoiceStatus.PENDING
    
    # Verify modified has changes
    assert modified.status == InvoiceStatus.PAID
    
    # Verify different instances
    assert original is not modified
```

### 7. Exception Testing

```python
def test_invoice_mark_as_paid_from_paid_raises():
    """Test cannot mark paid invoice as paid again."""
    invoice = Invoice(status=InvoiceStatus.PAID, ...)
    
    with pytest.raises(InvalidStateTransition) as exc_info:
        invoice.mark_as_paid(now)
    
    assert "Cannot mark as paid from status: paid" in str(exc_info.value)
```

---

## Git Workflow

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/{description}` | `feature/add-payment-entity` |
| Bug fix | `fix/{description}` | `fix/invoice-calculation-error` |
| ADR | `adr/{number}-{description}` | `adr/002-domain-model` |
| Refactor | `refactor/{description}` | `refactor/extract-money-value-object` |

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
feat(domain): add Invoice entity with copy-on-write pattern

Implements immutable Invoice entity following ADR-001 standards.
All state changes return new instances via dataclasses.replace().

- Add Invoice dataclass with frozen=True, slots=True
- Implement mark_as_paid() and record_payment() methods
- Add comprehensive unit tests

Fixes #45
```

```
fix(repository): correct Decimal conversion in invoice mapper

Invoice amounts were being converted to float in PostgresInvoiceRepository,
causing precision loss. Now properly converts to Decimal from NUMERIC column.

BREAKING CHANGE: InvoiceModel.amount now returns Decimal, not float
```

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
2. **Architecture**: Follows Clean Architecture and ADR-001?
3. **Immutability**: Uses frozen dataclasses and copy-on-write?
4. **Domain purity**: Domain doesn't access external resources?
5. **Type safety**: Complete type hints, mypy passes?
6. **Tests**: Adequate coverage, testing immutability?
7. **Documentation**: Clear docstrings, ADR if needed?
8. **Simplicity**: Is it as simple as possible?
