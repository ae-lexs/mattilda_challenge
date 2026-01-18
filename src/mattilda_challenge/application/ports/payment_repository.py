from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId, StudentId


class PaymentRepository(ABC):
    """
    Port for payment data access.

    All implementations must inherit from this class and implement
    all abstract methods.
    """

    @abstractmethod
    async def get_by_id(
        self,
        payment_id: PaymentId,
        for_update: bool = False,
    ) -> Payment | None:
        """
        Get payment by ID or None if not found.

        Args:
            payment_id: Unique payment identifier
            for_update: If True, acquire row lock

        Returns:
            Payment entity or None if not found
        """
        ...

    @abstractmethod
    async def save(self, payment: Payment) -> Payment:
        """
        Save payment entity to persistence.

        Args:
            payment: Payment entity to save

        Returns:
            Saved payment
        """
        ...

    @abstractmethod
    async def find(
        self,
        filters: PaymentFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Payment]:
        """
        Find payments matching filters with pagination.

        Args:
            filters: Filter criteria (invoice_id, payment_date range)
            pagination: Offset and limit
            sort: Sort field and direction

        Returns:
            Page containing matching payments and metadata
        """
        ...

    @abstractmethod
    async def get_total_by_invoice(self, invoice_id: InvoiceId) -> Decimal:
        """
        Get total payments made against an invoice.

        CRITICAL for payment recording use case:
        - Determines remaining balance
        - Prevents overpayment

        Args:
            invoice_id: Invoice to sum payments for

        Returns:
            Sum of all payment amounts (Decimal), 0 if no payments
        """
        ...

    @abstractmethod
    async def get_total_by_student(self, student_id: StudentId) -> Decimal:
        """
        Get total payments made by a student (across all invoices).

        Used for account statement calculations.

        Args:
            student_id: Student to sum payments for

        Returns:
            Sum of all payment amounts (Decimal)
        """
        ...

    @abstractmethod
    async def find_by_invoice(
        self,
        invoice_id: InvoiceId,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Payment]:
        """
        Find all payments for a specific invoice.

        Convenience method for common query pattern.

        Args:
            invoice_id: Invoice to get payments for
            pagination: Offset and limit
            sort: Sort field and direction

        Returns:
            Page containing invoice's payments
        """
        ...
