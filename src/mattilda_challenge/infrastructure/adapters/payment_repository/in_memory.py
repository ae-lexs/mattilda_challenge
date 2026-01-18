from __future__ import annotations

from decimal import Decimal

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.application.ports import PaymentRepository
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId, StudentId


class InMemoryPaymentRepository(PaymentRepository):
    """
    In-memory implementation of PaymentRepository for testing.

    Stores entities in a dictionary. Does not persist between test runs.
    Used in unit tests to verify use case behavior without database.
    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._payments: dict[PaymentId, Payment] = {}
        # For get_total_by_student, we need to track invoice->student mapping
        # This is injected via set_invoice_student_mapping for testing
        self._invoice_to_student: dict[InvoiceId, StudentId] = {}

    async def get_by_id(
        self,
        payment_id: PaymentId,
        for_update: bool = False,  # noqa: ARG002
    ) -> Payment | None:
        """
        Get payment by ID.

        Note: for_update is ignored in memory implementation
        (no concurrent access in unit tests).
        """
        return self._payments.get(payment_id)

    async def save(self, payment: Payment) -> Payment:
        """Save payment to in-memory storage."""
        self._payments[payment.id] = payment
        return payment

    async def find(
        self,
        filters: PaymentFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Payment]:
        """Find payments with filtering, sorting, and pagination."""
        # Filter
        items = list(self._payments.values())
        items = self._apply_filters(items, filters)

        # Sort
        items = self._apply_sort(items, sort)

        # Count before pagination
        total = len(items)

        # Paginate
        start = pagination.offset
        end = start + pagination.limit
        items = items[start:end]

        return Page(
            items=tuple(items),
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
        )

    async def get_total_by_invoice(self, invoice_id: InvoiceId) -> Decimal:
        """Get total payments made against an invoice."""
        total = Decimal("0")
        for payment in self._payments.values():
            if payment.invoice_id == invoice_id:
                total += payment.amount
        return total

    async def get_total_by_student(self, student_id: StudentId) -> Decimal:
        """
        Get total payments made by a student (across all invoices).

        Note: Requires invoice->student mapping to be set via
        set_invoice_student_mapping() for accurate results.
        """
        total = Decimal("0")
        for payment in self._payments.values():
            # Look up which student owns this invoice
            mapped_student = self._invoice_to_student.get(payment.invoice_id)
            if mapped_student == student_id:
                total += payment.amount
        return total

    async def find_by_invoice(
        self,
        invoice_id: InvoiceId,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Payment]:
        """Find all payments for an invoice."""
        filters = PaymentFilters(invoice_id=invoice_id.value)
        return await self.find(filters, pagination, sort)

    def _apply_filters(
        self,
        items: list[Payment],
        filters: PaymentFilters,
    ) -> list[Payment]:
        """Apply filter criteria to payment list."""
        result = items

        if filters.invoice_id is not None:
            result = [p for p in result if p.invoice_id.value == filters.invoice_id]

        if filters.payment_date_from is not None:
            result = [p for p in result if p.payment_date >= filters.payment_date_from]

        if filters.payment_date_to is not None:
            result = [p for p in result if p.payment_date <= filters.payment_date_to]

        return result

    def _apply_sort(
        self,
        items: list[Payment],
        sort: SortParams,
    ) -> list[Payment]:
        """Apply sorting to payment list."""
        sort_key_map = {
            "created_at": lambda p: (p.created_at, p.id.value),
            "payment_date": lambda p: (p.payment_date, p.id.value),
            "amount": lambda p: (p.amount, p.id.value),
        }

        key_func = sort_key_map.get(sort.sort_by, sort_key_map["created_at"])
        reverse = sort.sort_order == "desc"

        return sorted(items, key=key_func, reverse=reverse)

    # Test helper methods (not part of port interface)

    def clear(self) -> None:
        """Clear all stored payments (test utility)."""
        self._payments.clear()
        self._invoice_to_student.clear()

    def add(self, payment: Payment) -> None:
        """Add payment directly (test utility for setup)."""
        self._payments[payment.id] = payment

    def set_invoice_student_mapping(
        self, invoice_id: InvoiceId, student_id: StudentId
    ) -> None:
        """
        Set invoice->student mapping for get_total_by_student.

        This is needed because in-memory implementation cannot join
        through the invoice table like PostgreSQL can.

        Args:
            invoice_id: Invoice ID
            student_id: Student who owns the invoice
        """
        self._invoice_to_student[invoice_id] = student_id
