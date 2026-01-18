from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from mattilda_challenge.domain.exceptions import (
    InvalidInvoiceAmountError,
    InvalidInvoiceDataError,
    InvalidStateTransitionError,
)
from mattilda_challenge.domain.validate_utc_timestamp import validate_utc_timestamp
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    StudentId,
)


@dataclass(frozen=True, slots=True)
class Invoice:
    """
    Invoice entity representing a billing invoice issued to a student.

    Supports partial payments (multiple Payment entities can reference this invoice).

    **Status management**: Status is STORED (not calculated). Use cases are responsible
    for updating status when payments are recorded. The domain entity validates that
    transitions are legal, but does not calculate the new status—that's the use case's job.

    **Late fees**: Calculated via LateFeePolicy value object, which encapsulates the
    "original amount vs balance" business rule.

    Immutable. Changes return new instances via copy-on-write.
    """

    id: InvoiceId
    student_id: StudentId
    invoice_number: str  # Human-readable: "INV-2024-001"
    amount: Decimal  # Total amount to be paid (NEVER float)
    due_date: datetime
    description: str
    late_fee_policy: LateFeePolicy  # Encapsulates late fee calculation
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate invariants at construction."""
        # Check type FIRST, before any comparisons
        if not isinstance(self.amount, Decimal):
            raise InvalidInvoiceAmountError(
                f"Invoice amount must be Decimal, got {type(self.amount).__name__}"
            )

        if self.amount <= Decimal("0"):
            raise InvalidInvoiceAmountError(
                f"Invoice amount must be positive, got {self.amount}"
            )

        if not self.invoice_number or not self.invoice_number.strip():
            raise InvalidInvoiceDataError("Invoice number cannot be empty")

        if not self.description or not self.description.strip():
            raise InvalidInvoiceDataError("Invoice description cannot be empty")

        # UTC validation via reusable guard (see Section 4.4)
        validate_utc_timestamp(self.due_date, "due_date")
        validate_utc_timestamp(self.created_at, "created_at")
        validate_utc_timestamp(self.updated_at, "updated_at")

        if self.due_date < self.created_at:
            raise InvalidInvoiceDataError(
                f"Due date {self.due_date} cannot be before creation {self.created_at}"
            )

    @classmethod
    def create(
        cls,
        student_id: StudentId,
        amount: Decimal,
        due_date: datetime,
        description: str,
        late_fee_policy: LateFeePolicy,
        now: datetime,
    ) -> Invoice:
        """
        Create new invoice with generated ID and invoice number.

        Args:
            student_id: Student being invoiced
            amount: Total invoice amount (must be positive Decimal)
            due_date: Payment due date
            description: Invoice description/concept
            late_fee_policy: Policy for late fee calculation
            now: Current timestamp (injected)

        Returns:
            New invoice with PENDING status
        """
        return cls(
            id=InvoiceId.generate(),
            student_id=student_id,
            invoice_number=cls._generate_invoice_number(now),
            amount=amount,
            due_date=due_date,
            description=description.strip(),
            late_fee_policy=late_fee_policy,
            status=InvoiceStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _generate_invoice_number(now: datetime) -> str:
        """
        Generate human-readable invoice number.

        Format: INV-YYYY-NNNNNN (e.g., INV-2024-000001)

        **IMPORTANT**: This is a DECORATIVE field for human readability only.
        Uniqueness is NOT guaranteed—timestamp-based suffix can collide under load
        or across multiple application instances.

        The UUID `id` field is the true unique identifier.

        **Production implementation**: Replace with DB-backed sequence per school/year:
        ```sql
        SELECT COALESCE(MAX(CAST(SUBSTRING(invoice_number FROM 10) AS INTEGER)), 0) + 1
        FROM invoices
        WHERE invoice_number LIKE 'INV-2024-%'
        ```

        For this challenge, we accept potential collisions and treat invoice_number
        as display-only.
        """
        year = now.year
        # Timestamp-based suffix (NOT UNIQUE - may collide)
        timestamp_suffix = int(now.timestamp() * 1000) % 1000000
        return f"INV-{year}-{timestamp_suffix:06d}"

    def is_overdue(self, now: datetime) -> bool:
        """
        Check if invoice is overdue (calculated, not stored).

        An invoice is overdue if:
        - Current time is past due date AND
        - Status is PENDING or PARTIALLY_PAID

        Args:
            now: Current timestamp (injected)

        Returns:
            True if invoice is overdue
        """
        return now > self.due_date and self.status in [
            InvoiceStatus.PENDING,
            InvoiceStatus.PARTIALLY_PAID,
        ]

    def calculate_late_fee(self, now: datetime) -> Decimal:
        """
        Calculate late fee using policy.

        Delegates to LateFeePolicy to ensure consistent calculation
        and centralize "original amount vs balance" business rule.

        Args:
            now: Current timestamp (injected)

        Returns:
            Late fee amount (Decimal, rounded to cents)
            Returns Decimal("0.00") if not overdue
        """
        if not self.is_overdue(now):
            return Decimal("0.00")

        return self.late_fee_policy.calculate_fee(
            original_amount=self.amount,  # Explicitly ORIGINAL amount
            due_date=self.due_date,
            now=now,
        )

    def update_status(self, new_status: InvoiceStatus, now: datetime) -> Invoice:
        """
        Return new invoice with updated status.

        Validates state transitions are legal.

        Args:
            new_status: Target status
            now: Current timestamp (injected)

        Returns:
            New invoice instance with updated status

        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        # Validate transition
        if not self._is_valid_transition(self.status, new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        return replace(self, status=new_status, updated_at=now)

    def cancel(self, now: datetime) -> Invoice:
        """
        Return new invoice with status CANCELLED.

        Args:
            now: Current timestamp (injected)

        Returns:
            New invoice with CANCELLED status

        Raises:
            InvalidStateTransitionError: If invoice is already PAID
        """
        if self.status == InvoiceStatus.PAID:
            raise InvalidStateTransitionError("Cannot cancel paid invoice")

        return replace(self, status=InvoiceStatus.CANCELLED, updated_at=now)

    @staticmethod
    def _is_valid_transition(current: InvoiceStatus, target: InvoiceStatus) -> bool:
        """
        Check if status transition is valid.

        Valid transitions:
        - PENDING → PARTIALLY_PAID, PAID, CANCELLED
        - PARTIALLY_PAID → PAID, CANCELLED
        - PAID → (terminal, no transitions)
        - CANCELLED → (terminal, no transitions)
        """
        if current == target:
            return True  # Same status is always allowed

        allowed_transitions = {
            InvoiceStatus.PENDING: {
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.PAID,
                InvoiceStatus.CANCELLED,
            },
            InvoiceStatus.PARTIALLY_PAID: {
                InvoiceStatus.PAID,
                InvoiceStatus.CANCELLED,
            },
            InvoiceStatus.PAID: set(),  # Terminal
            InvoiceStatus.CANCELLED: set(),  # Terminal
        }

        return target in allowed_transitions.get(current, set())
