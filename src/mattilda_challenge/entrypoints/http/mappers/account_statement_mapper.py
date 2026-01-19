"""Account statement mapper for DTO <-> domain model translation."""

from __future__ import annotations

from mattilda_challenge.application.dtos import (
    SchoolAccountStatement,
    StudentAccountStatement,
)
from mattilda_challenge.entrypoints.http.dtos import (
    SchoolAccountStatementDTO,
    StudentAccountStatementDTO,
)


class AccountStatementMapper:
    """Maps between Account Statement DTOs and domain models."""

    @staticmethod
    def to_student_response(
        statement: StudentAccountStatement,
    ) -> StudentAccountStatementDTO:
        """
        Convert domain student account statement to REST response DTO.

        Handles:
        - UUID value objects → str
        - Decimal → str (monetary values)
        - datetime → str (ISO 8601 format)
        """
        return StudentAccountStatementDTO(
            student_id=str(statement.student_id.value),
            student_name=statement.student_name,
            school_name=statement.school_name,
            total_invoiced=str(statement.total_invoiced),
            total_paid=str(statement.total_paid),
            total_pending=str(statement.total_pending),
            invoices_pending=statement.invoices_pending,
            invoices_partially_paid=statement.invoices_partially_paid,
            invoices_paid=statement.invoices_paid,
            invoices_cancelled=statement.invoices_cancelled,
            invoices_overdue=statement.invoices_overdue,
            total_late_fees=str(statement.total_late_fees),
            statement_date=statement.statement_date.isoformat().replace("+00:00", "Z"),
        )

    @staticmethod
    def to_school_response(
        statement: SchoolAccountStatement,
    ) -> SchoolAccountStatementDTO:
        """
        Convert domain school account statement to REST response DTO.

        Handles:
        - UUID value objects → str
        - Decimal → str (monetary values)
        - datetime → str (ISO 8601 format)
        """
        return SchoolAccountStatementDTO(
            school_id=str(statement.school_id.value),
            school_name=statement.school_name,
            total_students=statement.total_students,
            active_students=statement.active_students,
            total_invoiced=str(statement.total_invoiced),
            total_paid=str(statement.total_paid),
            total_pending=str(statement.total_pending),
            invoices_pending=statement.invoices_pending,
            invoices_partially_paid=statement.invoices_partially_paid,
            invoices_paid=statement.invoices_paid,
            invoices_overdue=statement.invoices_overdue,
            invoices_cancelled=statement.invoices_cancelled,
            total_late_fees=str(statement.total_late_fees),
            statement_date=statement.statement_date.isoformat().replace("+00:00", "Z"),
        )
