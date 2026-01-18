from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import InvoiceId, StudentId


class InvoiceRepository(ABC):
    """
    Port for invoice data access.

    All implementations must inherit from this class and implement
    all abstract methods.
    """

    @abstractmethod
    async def get_by_id(
        self,
        invoice_id: InvoiceId,
        for_update: bool = False,
    ) -> Invoice | None:
        """
        Get invoice by ID or None if not found.

        IMPORTANT: Use for_update=True when recording payments to
        prevent concurrent modification race conditions.

        Args:
            invoice_id: Unique invoice identifier
            for_update: If True, acquire row lock (SELECT ... FOR UPDATE)

        Returns:
            Invoice entity or None if not found
        """
        ...

    @abstractmethod
    async def save(self, invoice: Invoice) -> Invoice:
        """
        Save invoice entity to persistence.

        Args:
            invoice: Invoice entity to save

        Returns:
            Saved invoice
        """
        ...

    @abstractmethod
    async def find(
        self,
        filters: InvoiceFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Invoice]:
        """
        Find invoices matching filters with pagination.

        Args:
            filters: Filter criteria (student_id, school_id, status, due_date range)
            pagination: Offset and limit
            sort: Sort field and direction

        Returns:
            Page containing matching invoices and metadata
        """
        ...

    @abstractmethod
    async def find_by_student(
        self,
        student_id: StudentId,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Invoice]:
        """
        Find all invoices for a specific student.

        Convenience method for common query pattern.

        Args:
            student_id: Student to get invoices for
            pagination: Offset and limit
            sort: Sort field and direction

        Returns:
            Page containing student's invoices
        """
        ...

    @abstractmethod
    async def get_total_amount_by_student(self, student_id: StudentId) -> Decimal:
        """
        Get total invoiced amount for a student.

        Used for account statement calculations.

        Args:
            student_id: Student to calculate total for

        Returns:
            Sum of all invoice amounts (Decimal)
        """
        ...
