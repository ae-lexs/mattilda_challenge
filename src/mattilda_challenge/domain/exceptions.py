"""
Domain exceptions for the Mattilda billing system.

All domain-specific errors inherit from DomainError base class.
Exceptions are organized by category: validation, entity-specific, and business rules.
"""

from __future__ import annotations

# =============================================================================
# Base Exception
# =============================================================================


class DomainError(Exception):
    """
    Base exception for all domain errors.

    All domain-specific exceptions inherit from this class,
    enabling catch-all handling at application boundaries.
    """

    pass


# =============================================================================
# Validation Errors - General
# =============================================================================


class ValidationError(DomainError):
    """Base class for validation errors."""

    pass


class InvalidTimestampError(ValidationError):
    """Raised when a timestamp is naive or not in UTC timezone."""

    pass


class InvalidAmountError(ValidationError):
    """Raised when a monetary amount is invalid (not Decimal or non-positive)."""

    pass


# =============================================================================
# Entity ID Errors
# =============================================================================


class InvalidIdError(ValidationError):
    """Base class for invalid entity ID errors."""

    pass


class InvalidSchoolIdError(InvalidIdError):
    """Raised when a school ID is invalid."""

    pass


class InvalidStudentIdError(InvalidIdError):
    """Raised when a student ID is invalid."""

    pass


class InvalidInvoiceIdError(InvalidIdError):
    """Raised when an invoice ID is invalid."""

    pass


class InvalidPaymentIdError(InvalidIdError):
    """Raised when a payment ID is invalid."""

    pass


# =============================================================================
# School Errors
# =============================================================================


class SchoolError(DomainError):
    """Base class for school-related errors."""

    pass


class InvalidSchoolDataError(SchoolError):
    """Raised when school data is invalid (empty name, address, etc.)."""

    pass


class SchoolNotFoundError(SchoolError):
    """Raised when a school is not found."""

    pass


# =============================================================================
# Student Errors
# =============================================================================


class StudentError(DomainError):
    """Base class for student-related errors."""

    pass


class InvalidStudentDataError(StudentError):
    """Raised when student data is invalid (empty name, invalid email, etc.)."""

    pass


class StudentNotFoundError(StudentError):
    """Raised when a student is not found."""

    pass


# =============================================================================
# Invoice Errors
# =============================================================================


class InvoiceError(DomainError):
    """Base class for invoice-related errors."""

    pass


class InvalidInvoiceDataError(InvoiceError):
    """Raised when invoice data is invalid (empty description, invalid dates, etc.)."""

    pass


class InvalidInvoiceAmountError(InvoiceError):
    """Raised when invoice amount is invalid (not Decimal, non-positive, etc.)."""

    pass


class InvalidLateFeeRateError(InvoiceError):
    """Raised when late fee rate is invalid (not Decimal, out of range 0-1)."""

    pass


class InvoiceNotFoundError(InvoiceError):
    """Raised when an invoice is not found."""

    pass


class InvalidStateTransitionError(InvoiceError):
    """Raised when an invoice state transition is not allowed."""

    pass


class CannotPayCancelledInvoiceError(InvoiceError):
    """Raised when attempting to pay a cancelled invoice."""

    pass


# =============================================================================
# Payment Errors
# =============================================================================


class PaymentError(DomainError):
    """Base class for payment-related errors."""

    pass


class InvalidPaymentDataError(PaymentError):
    """Raised when payment data is invalid (empty method, invalid dates, etc.)."""

    pass


class InvalidPaymentAmountError(PaymentError):
    """Raised when payment amount is invalid (not Decimal, non-positive, etc.)."""

    pass


class PaymentNotFoundError(PaymentError):
    """Raised when a payment is not found."""

    pass


class PaymentExceedsInvoiceAmountError(PaymentError):
    """Raised when total payments exceed the invoice amount."""

    pass


class PaymentExceedsBalanceError(PaymentError):
    """Raised when a payment exceeds the remaining balance due."""

    pass
