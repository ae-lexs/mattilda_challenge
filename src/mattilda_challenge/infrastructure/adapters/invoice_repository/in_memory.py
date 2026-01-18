from __future__ import annotations

from decimal import Decimal

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.application.ports import InvoiceRepository
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import InvoiceId, StudentId


class InMemoryInvoiceRepository(InvoiceRepository):
    """
    In-memory implementation of InvoiceRepository for testing.

    Stores entities in a dictionary. Does not persist between test runs.
    Used in unit tests to verify use case behavior without database.
    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._invoices: dict[InvoiceId, Invoice] = {}

    async def get_by_id(
        self,
        invoice_id: InvoiceId,
        for_update: bool = False,  # noqa: ARG002
    ) -> Invoice | None:
        """
        Get invoice by ID.

        Note: for_update is ignored in memory implementation
        (no concurrent access in unit tests).
        """
        return self._invoices.get(invoice_id)

    async def save(self, invoice: Invoice) -> Invoice:
        """Save invoice to in-memory storage."""
        self._invoices[invoice.id] = invoice
        return invoice

    async def find(
        self,
        filters: InvoiceFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Invoice]:
        """Find invoices with filtering, sorting, and pagination."""
        # Filter
        items = list(self._invoices.values())
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

    async def find_by_student(
        self,
        student_id: StudentId,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Invoice]:
        """Find all invoices for a student."""
        filters = InvoiceFilters(student_id=student_id.value)
        return await self.find(filters, pagination, sort)

    async def get_total_amount_by_student(self, student_id: StudentId) -> Decimal:
        """Get sum of all invoice amounts for a student."""
        total = Decimal("0")
        for invoice in self._invoices.values():
            if invoice.student_id == student_id:
                total += invoice.amount
        return total

    def _apply_filters(
        self,
        items: list[Invoice],
        filters: InvoiceFilters,
    ) -> list[Invoice]:
        """Apply filter criteria to invoice list."""
        result = items

        if filters.student_id is not None:
            result = [i for i in result if i.student_id.value == filters.student_id]

        if filters.status is not None:
            result = [i for i in result if i.status.value == filters.status]

        if filters.due_date_from is not None:
            result = [i for i in result if i.due_date >= filters.due_date_from]

        if filters.due_date_to is not None:
            result = [i for i in result if i.due_date <= filters.due_date_to]

        # LIMITATION: school_id filter requires access to StudentRepository.
        # In-memory repositories cannot perform cross-aggregate filtering.
        # For unit tests, either:
        # 1. Pre-filter test data to students from a single school
        # 2. Use integration tests for school_id filtering scenarios
        # See Section 4.3 for testing guidelines.

        return result

    def _apply_sort(
        self,
        items: list[Invoice],
        sort: SortParams,
    ) -> list[Invoice]:
        """Apply sorting to invoice list."""
        sort_key_map = {
            "created_at": lambda i: (i.created_at, i.id.value),
            "due_date": lambda i: (i.due_date, i.id.value),
            "amount": lambda i: (i.amount, i.id.value),
            "status": lambda i: (i.status.value, i.id.value),
        }

        key_func = sort_key_map.get(sort.sort_by, sort_key_map["created_at"])
        reverse = sort.sort_order == "desc"

        return sorted(items, key=key_func, reverse=reverse)

    # Test helper methods (not part of port interface)

    def clear(self) -> None:
        """Clear all stored invoices (test utility)."""
        self._invoices.clear()

    def add(self, invoice: Invoice) -> None:
        """Add invoice directly (test utility for setup)."""
        self._invoices[invoice.id] = invoice
