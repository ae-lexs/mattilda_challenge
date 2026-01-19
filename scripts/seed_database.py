#!/usr/bin/env python3
"""
Idempotent database seed script.

Creates sample schools, students, invoices, and payments for development/testing.
Uses fixed UUIDs so the script can be run multiple times safely.

Usage:
    uv run python scripts/seed_database.py
    # or via make:
    make seed
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.infrastructure.postgres.database import get_session_factory
from mattilda_challenge.infrastructure.postgres.models import (
    InvoiceModel,
    PaymentModel,
    SchoolModel,
    StudentModel,
)

# =============================================================================
# Fixed UUIDs for idempotent seeding
# =============================================================================

# Schools
SCHOOL_1_ID = UUID("10000000-0000-0000-0000-000000000001")
SCHOOL_2_ID = UUID("10000000-0000-0000-0000-000000000002")
SCHOOL_3_ID = UUID("10000000-0000-0000-0000-000000000003")

# Students (School 1)
STUDENT_1_ID = UUID("20000000-0000-0000-0000-000000000001")
STUDENT_2_ID = UUID("20000000-0000-0000-0000-000000000002")
STUDENT_3_ID = UUID("20000000-0000-0000-0000-000000000003")

# Students (School 2)
STUDENT_4_ID = UUID("20000000-0000-0000-0000-000000000004")
STUDENT_5_ID = UUID("20000000-0000-0000-0000-000000000005")

# Students (School 3)
STUDENT_6_ID = UUID("20000000-0000-0000-0000-000000000006")

# Invoices
INVOICE_1_ID = UUID("30000000-0000-0000-0000-000000000001")
INVOICE_2_ID = UUID("30000000-0000-0000-0000-000000000002")
INVOICE_3_ID = UUID("30000000-0000-0000-0000-000000000003")
INVOICE_4_ID = UUID("30000000-0000-0000-0000-000000000004")
INVOICE_5_ID = UUID("30000000-0000-0000-0000-000000000005")
INVOICE_6_ID = UUID("30000000-0000-0000-0000-000000000006")
INVOICE_7_ID = UUID("30000000-0000-0000-0000-000000000007")
INVOICE_8_ID = UUID("30000000-0000-0000-0000-000000000008")

# Payments
PAYMENT_1_ID = UUID("40000000-0000-0000-0000-000000000001")
PAYMENT_2_ID = UUID("40000000-0000-0000-0000-000000000002")
PAYMENT_3_ID = UUID("40000000-0000-0000-0000-000000000003")
PAYMENT_4_ID = UUID("40000000-0000-0000-0000-000000000004")
PAYMENT_5_ID = UUID("40000000-0000-0000-0000-000000000005")

# =============================================================================
# Seed Data
# =============================================================================

# Base timestamp for seed data
BASE_TIME = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)


def get_schools() -> list[dict]:
    """Get school seed data."""
    return [
        {
            "id": SCHOOL_1_ID,
            "name": "Colegio Montessori del Valle",
            "address": "Av. Insurgentes Sur 1234, Col. Del Valle, CDMX, 03100",
            "created_at": BASE_TIME,
        },
        {
            "id": SCHOOL_2_ID,
            "name": "Instituto Tecnologico de Monterrey",
            "address": "Calle Eugenio Garza Sada 2501, Monterrey, NL, 64849",
            "created_at": BASE_TIME + timedelta(days=1),
        },
        {
            "id": SCHOOL_3_ID,
            "name": "Escuela Primaria Benito Juarez",
            "address": "Calle 5 de Mayo 100, Centro, Guadalajara, JAL, 44100",
            "created_at": BASE_TIME + timedelta(days=2),
        },
    ]


def get_students() -> list[dict]:
    """Get student seed data."""
    return [
        # School 1 students
        {
            "id": STUDENT_1_ID,
            "school_id": SCHOOL_1_ID,
            "first_name": "Sofia",
            "last_name": "Garcia Martinez",
            "email": "sofia.garcia@example.com",
            "enrollment_date": BASE_TIME,
            "status": "active",
            "created_at": BASE_TIME,
            "updated_at": BASE_TIME,
        },
        {
            "id": STUDENT_2_ID,
            "school_id": SCHOOL_1_ID,
            "first_name": "Diego",
            "last_name": "Hernandez Lopez",
            "email": "diego.hernandez@example.com",
            "enrollment_date": BASE_TIME + timedelta(days=30),
            "status": "active",
            "created_at": BASE_TIME + timedelta(days=30),
            "updated_at": BASE_TIME + timedelta(days=30),
        },
        {
            "id": STUDENT_3_ID,
            "school_id": SCHOOL_1_ID,
            "first_name": "Valentina",
            "last_name": "Rodriguez Sanchez",
            "email": "valentina.rodriguez@example.com",
            "enrollment_date": BASE_TIME + timedelta(days=60),
            "status": "inactive",
            "created_at": BASE_TIME + timedelta(days=60),
            "updated_at": BASE_TIME + timedelta(days=120),
        },
        # School 2 students
        {
            "id": STUDENT_4_ID,
            "school_id": SCHOOL_2_ID,
            "first_name": "Santiago",
            "last_name": "Ramirez Torres",
            "email": "santiago.ramirez@example.com",
            "enrollment_date": BASE_TIME + timedelta(days=15),
            "status": "active",
            "created_at": BASE_TIME + timedelta(days=15),
            "updated_at": BASE_TIME + timedelta(days=15),
        },
        {
            "id": STUDENT_5_ID,
            "school_id": SCHOOL_2_ID,
            "first_name": "Isabella",
            "last_name": "Flores Morales",
            "email": "isabella.flores@example.com",
            "enrollment_date": BASE_TIME + timedelta(days=45),
            "status": "graduated",
            "created_at": BASE_TIME + timedelta(days=45),
            "updated_at": BASE_TIME + timedelta(days=365),
        },
        # School 3 students
        {
            "id": STUDENT_6_ID,
            "school_id": SCHOOL_3_ID,
            "first_name": "Mateo",
            "last_name": "Gonzalez Diaz",
            "email": "mateo.gonzalez@example.com",
            "enrollment_date": BASE_TIME + timedelta(days=20),
            "status": "active",
            "created_at": BASE_TIME + timedelta(days=20),
            "updated_at": BASE_TIME + timedelta(days=20),
        },
    ]


def get_invoices() -> list[dict]:
    """Get invoice seed data."""
    return [
        # Sofia's invoices (School 1)
        {
            "id": INVOICE_1_ID,
            "student_id": STUDENT_1_ID,
            "invoice_number": "INV-2024-000001",
            "amount": Decimal("5500.00"),
            "due_date": BASE_TIME + timedelta(days=30),
            "description": "Colegiatura Enero 2024",
            "late_fee_policy_monthly_rate": Decimal("0.05"),
            "status": "paid",
            "created_at": BASE_TIME,
            "updated_at": BASE_TIME + timedelta(days=25),
        },
        {
            "id": INVOICE_2_ID,
            "student_id": STUDENT_1_ID,
            "invoice_number": "INV-2024-000002",
            "amount": Decimal("5500.00"),
            "due_date": BASE_TIME + timedelta(days=60),
            "description": "Colegiatura Febrero 2024",
            "late_fee_policy_monthly_rate": Decimal("0.05"),
            "status": "partially_paid",
            "created_at": BASE_TIME + timedelta(days=30),
            "updated_at": BASE_TIME + timedelta(days=55),
        },
        {
            "id": INVOICE_3_ID,
            "student_id": STUDENT_1_ID,
            "invoice_number": "INV-2024-000003",
            "amount": Decimal("5500.00"),
            "due_date": BASE_TIME + timedelta(days=90),
            "description": "Colegiatura Marzo 2024",
            "late_fee_policy_monthly_rate": Decimal("0.05"),
            "status": "pending",
            "created_at": BASE_TIME + timedelta(days=60),
            "updated_at": BASE_TIME + timedelta(days=60),
        },
        # Diego's invoices (School 1)
        {
            "id": INVOICE_4_ID,
            "student_id": STUDENT_2_ID,
            "invoice_number": "INV-2024-000004",
            "amount": Decimal("5500.00"),
            "due_date": BASE_TIME + timedelta(days=60),
            "description": "Colegiatura Febrero 2024",
            "late_fee_policy_monthly_rate": Decimal("0.05"),
            "status": "paid",
            "created_at": BASE_TIME + timedelta(days=30),
            "updated_at": BASE_TIME + timedelta(days=50),
        },
        # Santiago's invoices (School 2) - overdue
        {
            "id": INVOICE_5_ID,
            "student_id": STUDENT_4_ID,
            "invoice_number": "INV-2024-000005",
            "amount": Decimal("8500.00"),
            "due_date": BASE_TIME + timedelta(days=45),
            "description": "Colegiatura Febrero 2024",
            "late_fee_policy_monthly_rate": Decimal("0.03"),
            "status": "pending",  # Overdue!
            "created_at": BASE_TIME + timedelta(days=15),
            "updated_at": BASE_TIME + timedelta(days=15),
        },
        # Isabella's invoices (School 2)
        {
            "id": INVOICE_6_ID,
            "student_id": STUDENT_5_ID,
            "invoice_number": "INV-2024-000006",
            "amount": Decimal("8500.00"),
            "due_date": BASE_TIME + timedelta(days=75),
            "description": "Colegiatura Marzo 2024",
            "late_fee_policy_monthly_rate": Decimal("0.03"),
            "status": "paid",
            "created_at": BASE_TIME + timedelta(days=45),
            "updated_at": BASE_TIME + timedelta(days=70),
        },
        # Mateo's invoices (School 3)
        {
            "id": INVOICE_7_ID,
            "student_id": STUDENT_6_ID,
            "invoice_number": "INV-2024-000007",
            "amount": Decimal("3200.00"),
            "due_date": BASE_TIME + timedelta(days=50),
            "description": "Colegiatura Febrero 2024",
            "late_fee_policy_monthly_rate": Decimal("0.04"),
            "status": "paid",
            "created_at": BASE_TIME + timedelta(days=20),
            "updated_at": BASE_TIME + timedelta(days=45),
        },
        {
            "id": INVOICE_8_ID,
            "student_id": STUDENT_6_ID,
            "invoice_number": "INV-2024-000008",
            "amount": Decimal("3200.00"),
            "due_date": BASE_TIME + timedelta(days=80),
            "description": "Colegiatura Marzo 2024",
            "late_fee_policy_monthly_rate": Decimal("0.04"),
            "status": "cancelled",
            "created_at": BASE_TIME + timedelta(days=50),
            "updated_at": BASE_TIME + timedelta(days=55),
        },
    ]


def get_payments() -> list[dict]:
    """Get payment seed data."""
    return [
        # Sofia's payments
        {
            "id": PAYMENT_1_ID,
            "invoice_id": INVOICE_1_ID,
            "amount": Decimal("5500.00"),
            "payment_date": BASE_TIME + timedelta(days=25),
            "payment_method": "transferencia",
            "reference_number": "SPEI-2024-001",
            "created_at": BASE_TIME + timedelta(days=25),
        },
        {
            "id": PAYMENT_2_ID,
            "invoice_id": INVOICE_2_ID,
            "amount": Decimal("3000.00"),
            "payment_date": BASE_TIME + timedelta(days=55),
            "payment_method": "efectivo",
            "reference_number": None,
            "created_at": BASE_TIME + timedelta(days=55),
        },
        # Diego's payments
        {
            "id": PAYMENT_3_ID,
            "invoice_id": INVOICE_4_ID,
            "amount": Decimal("5500.00"),
            "payment_date": BASE_TIME + timedelta(days=50),
            "payment_method": "tarjeta_credito",
            "reference_number": "CC-2024-042",
            "created_at": BASE_TIME + timedelta(days=50),
        },
        # Isabella's payments
        {
            "id": PAYMENT_4_ID,
            "invoice_id": INVOICE_6_ID,
            "amount": Decimal("8500.00"),
            "payment_date": BASE_TIME + timedelta(days=70),
            "payment_method": "transferencia",
            "reference_number": "SPEI-2024-089",
            "created_at": BASE_TIME + timedelta(days=70),
        },
        # Mateo's payments
        {
            "id": PAYMENT_5_ID,
            "invoice_id": INVOICE_7_ID,
            "amount": Decimal("3200.00"),
            "payment_date": BASE_TIME + timedelta(days=45),
            "payment_method": "deposito",
            "reference_number": "DEP-2024-015",
            "created_at": BASE_TIME + timedelta(days=45),
        },
    ]


# =============================================================================
# Upsert Functions
# =============================================================================


async def upsert_schools(session: AsyncSession) -> int:
    """Upsert schools, returns count of affected rows."""
    schools = get_schools()
    stmt = insert(SchoolModel).values(schools)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "name": stmt.excluded.name,
            "address": stmt.excluded.address,
            "created_at": stmt.excluded.created_at,
        },
    )
    result = await session.execute(stmt)
    return result.rowcount


async def upsert_students(session: AsyncSession) -> int:
    """Upsert students, returns count of affected rows."""
    students = get_students()
    stmt = insert(StudentModel).values(students)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "school_id": stmt.excluded.school_id,
            "first_name": stmt.excluded.first_name,
            "last_name": stmt.excluded.last_name,
            "email": stmt.excluded.email,
            "enrollment_date": stmt.excluded.enrollment_date,
            "status": stmt.excluded.status,
            "created_at": stmt.excluded.created_at,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    result = await session.execute(stmt)
    return result.rowcount


async def upsert_invoices(session: AsyncSession) -> int:
    """Upsert invoices, returns count of affected rows."""
    invoices = get_invoices()
    stmt = insert(InvoiceModel).values(invoices)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "student_id": stmt.excluded.student_id,
            "invoice_number": stmt.excluded.invoice_number,
            "amount": stmt.excluded.amount,
            "due_date": stmt.excluded.due_date,
            "description": stmt.excluded.description,
            "late_fee_policy_monthly_rate": stmt.excluded.late_fee_policy_monthly_rate,
            "status": stmt.excluded.status,
            "created_at": stmt.excluded.created_at,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    result = await session.execute(stmt)
    return result.rowcount


async def upsert_payments(session: AsyncSession) -> int:
    """Upsert payments, returns count of affected rows."""
    payments = get_payments()
    stmt = insert(PaymentModel).values(payments)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "invoice_id": stmt.excluded.invoice_id,
            "amount": stmt.excluded.amount,
            "payment_date": stmt.excluded.payment_date,
            "payment_method": stmt.excluded.payment_method,
            "reference_number": stmt.excluded.reference_number,
            "created_at": stmt.excluded.created_at,
        },
    )
    result = await session.execute(stmt)
    return result.rowcount


# =============================================================================
# Main
# =============================================================================


async def seed_database() -> None:
    """Run the seed process."""
    print("Starting database seed...")
    print("-" * 50)

    session_factory = get_session_factory()

    async with session_factory() as session, session.begin():
        # Seed in order (respecting foreign key constraints)
        schools_count = await upsert_schools(session)
        print(f"Schools:  {schools_count} rows upserted")

        students_count = await upsert_students(session)
        print(f"Students: {students_count} rows upserted")

        invoices_count = await upsert_invoices(session)
        print(f"Invoices: {invoices_count} rows upserted")

        payments_count = await upsert_payments(session)
        print(f"Payments: {payments_count} rows upserted")

    print("-" * 50)
    print("Seed completed successfully!")

    # Print summary
    print("\nSeed Data Summary:")
    print("  - 3 schools (Colegio Montessori, Tec de Monterrey, Escuela Benito Juarez)")
    print("  - 6 students across schools")
    print("  - 8 invoices (various statuses: pending, paid, partially_paid, cancelled)")
    print("  - 5 payments")
    print("\nOverdue Invoice:")
    print("  - Santiago Ramirez (School 2): Invoice INV-2024-000005 for $8,500.00")


def main() -> None:
    """Entry point."""
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
