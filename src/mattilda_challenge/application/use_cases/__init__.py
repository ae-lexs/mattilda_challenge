"""Application use cases for the Mattilda billing system."""

from mattilda_challenge.application.use_cases.cancel_invoice import CancelInvoiceUseCase
from mattilda_challenge.application.use_cases.create_invoice import CreateInvoiceUseCase
from mattilda_challenge.application.use_cases.create_school import CreateSchoolUseCase
from mattilda_challenge.application.use_cases.create_student import CreateStudentUseCase
from mattilda_challenge.application.use_cases.delete_school import DeleteSchoolUseCase
from mattilda_challenge.application.use_cases.delete_student import DeleteStudentUseCase
from mattilda_challenge.application.use_cases.get_school_account_statement import (
    GetSchoolAccountStatementUseCase,
)
from mattilda_challenge.application.use_cases.get_student_account_statement import (
    GetStudentAccountStatementUseCase,
)
from mattilda_challenge.application.use_cases.list_invoices import ListInvoicesUseCase
from mattilda_challenge.application.use_cases.list_payments import ListPaymentsUseCase
from mattilda_challenge.application.use_cases.list_schools import ListSchoolsUseCase
from mattilda_challenge.application.use_cases.list_students import ListStudentsUseCase
from mattilda_challenge.application.use_cases.record_payment import RecordPaymentUseCase
from mattilda_challenge.application.use_cases.update_school import UpdateSchoolUseCase
from mattilda_challenge.application.use_cases.update_student import UpdateStudentUseCase

__all__ = [
    "CancelInvoiceUseCase",
    "CreateInvoiceUseCase",
    "CreateSchoolUseCase",
    "CreateStudentUseCase",
    "DeleteSchoolUseCase",
    "DeleteStudentUseCase",
    "GetSchoolAccountStatementUseCase",
    "GetStudentAccountStatementUseCase",
    "ListInvoicesUseCase",
    "ListPaymentsUseCase",
    "ListSchoolsUseCase",
    "ListStudentsUseCase",
    "RecordPaymentUseCase",
    "UpdateSchoolUseCase",
    "UpdateStudentUseCase",
]
