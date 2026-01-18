"""Tests for InvoiceMapper."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    StudentId,
)
from mattilda_challenge.infrastructure.postgres.mappers import InvoiceMapper
from mattilda_challenge.infrastructure.postgres.models import InvoiceModel


class TestInvoiceMapperToEntity:
    """Tests for InvoiceMapper.to_entity()."""

    def test_converts_model_to_entity(self) -> None:
        """Test that to_entity converts all fields correctly."""
        model_id = uuid4()
        student_id = uuid4()
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        due_date = now + timedelta(days=30)

        model = InvoiceModel(
            id=model_id,
            student_id=student_id,
            invoice_number="INV-2024-000001",
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition fee",
            late_fee_policy_monthly_rate=Decimal("0.0500"),
            status="pending",
            created_at=now,
            updated_at=now,
        )

        entity = InvoiceMapper.to_entity(model)

        assert isinstance(entity, Invoice)
        assert isinstance(entity.id, InvoiceId)
        assert isinstance(entity.student_id, StudentId)
        assert isinstance(entity.late_fee_policy, LateFeePolicy)
        assert entity.id.value == model_id
        assert entity.student_id.value == student_id
        assert entity.invoice_number == "INV-2024-000001"
        assert entity.amount == Decimal("1500.00")
        assert entity.due_date == due_date
        assert entity.description == "Tuition fee"
        assert entity.late_fee_policy.monthly_rate == Decimal("0.0500")
        assert entity.status == InvoiceStatus.PENDING
        assert entity.created_at == now
        assert entity.updated_at == now

    def test_converts_status_string_to_enum(self) -> None:
        """Test that status string is converted to InvoiceStatus enum."""
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        for status_str, expected_enum in [
            ("pending", InvoiceStatus.PENDING),
            ("partially_paid", InvoiceStatus.PARTIALLY_PAID),
            ("paid", InvoiceStatus.PAID),
            ("cancelled", InvoiceStatus.CANCELLED),
        ]:
            model = InvoiceModel(
                id=uuid4(),
                student_id=uuid4(),
                invoice_number=f"INV-{status_str}",
                amount=Decimal("100.00"),
                due_date=due_date,
                description="Test",
                late_fee_policy_monthly_rate=Decimal("0.05"),
                status=status_str,
                created_at=now,
                updated_at=now,
            )

            entity = InvoiceMapper.to_entity(model)

            assert entity.status == expected_enum

    def test_reconstructs_late_fee_policy_from_rate(self) -> None:
        """Test that LateFeePolicy is reconstructed from stored monthly rate."""
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        model = InvoiceModel(
            id=uuid4(),
            student_id=uuid4(),
            invoice_number="INV-TEST",
            amount=Decimal("1000.00"),
            due_date=due_date,
            description="Test",
            late_fee_policy_monthly_rate=Decimal("0.1000"),
            status="pending",
            created_at=now,
            updated_at=now,
        )

        entity = InvoiceMapper.to_entity(model)

        assert isinstance(entity.late_fee_policy, LateFeePolicy)
        assert entity.late_fee_policy.monthly_rate == Decimal("0.1000")


class TestInvoiceMapperToModel:
    """Tests for InvoiceMapper.to_model()."""

    def test_converts_entity_to_model(self) -> None:
        """Test that to_model converts all fields correctly."""
        invoice_id = InvoiceId.generate()
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        due_date = now + timedelta(days=30)

        entity = Invoice(
            id=invoice_id,
            student_id=student_id,
            invoice_number="INV-2024-000001",
            amount=Decimal("2000.00"),
            due_date=due_date,
            description="Lab fee",
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.0500")),
            status=InvoiceStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        model = InvoiceMapper.to_model(entity)

        assert isinstance(model, InvoiceModel)
        assert model.id == invoice_id.value
        assert model.student_id == student_id.value
        assert model.invoice_number == "INV-2024-000001"
        assert model.amount == Decimal("2000.00")
        assert model.due_date == due_date
        assert model.description == "Lab fee"
        assert model.late_fee_policy_monthly_rate == Decimal("0.0500")
        assert model.status == "pending"
        assert model.created_at == now
        assert model.updated_at == now

    def test_converts_status_enum_to_string(self) -> None:
        """Test that InvoiceStatus enum is converted to string."""
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        for status_enum, expected_str in [
            (InvoiceStatus.PENDING, "pending"),
            (InvoiceStatus.PARTIALLY_PAID, "partially_paid"),
            (InvoiceStatus.PAID, "paid"),
            (InvoiceStatus.CANCELLED, "cancelled"),
        ]:
            entity = Invoice(
                id=InvoiceId.generate(),
                student_id=StudentId.generate(),
                invoice_number="INV-TEST",
                amount=Decimal("100.00"),
                due_date=due_date,
                description="Test",
                late_fee_policy=LateFeePolicy.standard(),
                status=status_enum,
                created_at=now,
                updated_at=now,
            )

            model = InvoiceMapper.to_model(entity)

            assert model.status == expected_str

    def test_extracts_monthly_rate_from_policy(self) -> None:
        """Test that monthly rate is extracted from LateFeePolicy."""
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)
        policy = LateFeePolicy(monthly_rate=Decimal("0.0750"))

        entity = Invoice(
            id=InvoiceId.generate(),
            student_id=StudentId.generate(),
            invoice_number="INV-TEST",
            amount=Decimal("1000.00"),
            due_date=due_date,
            description="Test",
            late_fee_policy=policy,
            status=InvoiceStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        model = InvoiceMapper.to_model(entity)

        assert model.late_fee_policy_monthly_rate == Decimal("0.0750")


class TestInvoiceMapperRoundTrip:
    """Tests for round-trip conversion."""

    def test_entity_to_model_to_entity_preserves_data(self) -> None:
        """Test that entity -> model -> entity produces equivalent result."""
        student_id = StudentId.generate()
        now = datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC)
        due_date = now + timedelta(days=30)

        original = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Round trip invoice",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        model = InvoiceMapper.to_model(original)
        restored = InvoiceMapper.to_entity(model)

        assert restored == original

    def test_model_to_entity_to_model_preserves_data(self) -> None:
        """Test that model -> entity -> model produces equivalent data."""
        model_id = uuid4()
        student_id = uuid4()
        now = datetime(2024, 3, 20, 14, 0, 0, tzinfo=UTC)
        due_date = now + timedelta(days=45)

        original_model = InvoiceModel(
            id=model_id,
            student_id=student_id,
            invoice_number="INV-ROUND",
            amount=Decimal("2500.00"),
            due_date=due_date,
            description="Round trip test",
            late_fee_policy_monthly_rate=Decimal("0.0300"),
            status="partially_paid",
            created_at=now,
            updated_at=now,
        )

        entity = InvoiceMapper.to_entity(original_model)
        restored_model = InvoiceMapper.to_model(entity)

        assert restored_model.id == original_model.id
        assert restored_model.student_id == original_model.student_id
        assert restored_model.invoice_number == original_model.invoice_number
        assert restored_model.amount == original_model.amount
        assert restored_model.due_date == original_model.due_date
        assert restored_model.description == original_model.description
        assert (
            restored_model.late_fee_policy_monthly_rate
            == original_model.late_fee_policy_monthly_rate
        )
        assert restored_model.status == original_model.status
        assert restored_model.created_at == original_model.created_at
        assert restored_model.updated_at == original_model.updated_at
