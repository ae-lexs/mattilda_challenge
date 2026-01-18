"""Tests for PaymentMapper."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId
from mattilda_challenge.infrastructure.postgres.mappers import PaymentMapper
from mattilda_challenge.infrastructure.postgres.models import PaymentModel


class TestPaymentMapperToEntity:
    """Tests for PaymentMapper.to_entity()."""

    def test_converts_model_to_entity(self) -> None:
        """Test that to_entity converts all fields correctly."""
        model_id = uuid4()
        invoice_id = uuid4()
        payment_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        created_at = datetime(2024, 1, 15, 12, 5, 0, tzinfo=UTC)

        model = PaymentModel(
            id=model_id,
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=payment_date,
            payment_method="bank_transfer",
            reference_number="TXN-123456",
            created_at=created_at,
        )

        entity = PaymentMapper.to_entity(model)

        assert isinstance(entity, Payment)
        assert isinstance(entity.id, PaymentId)
        assert isinstance(entity.invoice_id, InvoiceId)
        assert entity.id.value == model_id
        assert entity.invoice_id.value == invoice_id
        assert entity.amount == Decimal("500.00")
        assert entity.payment_date == payment_date
        assert entity.payment_method == "bank_transfer"
        assert entity.reference_number == "TXN-123456"
        assert entity.created_at == created_at

    def test_handles_null_reference_number(self) -> None:
        """Test that None reference number is handled correctly."""
        now = datetime.now(UTC)

        model = PaymentModel(
            id=uuid4(),
            invoice_id=uuid4(),
            amount=Decimal("100.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            created_at=now,
        )

        entity = PaymentMapper.to_entity(model)

        assert entity.reference_number is None


class TestPaymentMapperToModel:
    """Tests for PaymentMapper.to_model()."""

    def test_converts_entity_to_model(self) -> None:
        """Test that to_model converts all fields correctly."""
        payment_id = PaymentId.generate()
        invoice_id = InvoiceId.generate()
        payment_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        created_at = datetime(2024, 1, 15, 12, 5, 0, tzinfo=UTC)

        entity = Payment(
            id=payment_id,
            invoice_id=invoice_id,
            amount=Decimal("750.00"),
            payment_date=payment_date,
            payment_method="card",
            reference_number="CARD-789",
            created_at=created_at,
        )

        model = PaymentMapper.to_model(entity)

        assert isinstance(model, PaymentModel)
        assert model.id == payment_id.value
        assert model.invoice_id == invoice_id.value
        assert model.amount == Decimal("750.00")
        assert model.payment_date == payment_date
        assert model.payment_method == "card"
        assert model.reference_number == "CARD-789"
        assert model.created_at == created_at

    def test_handles_null_reference_number(self) -> None:
        """Test that None reference number is handled correctly."""
        now = datetime.now(UTC)

        entity = Payment(
            id=PaymentId.generate(),
            invoice_id=InvoiceId.generate(),
            amount=Decimal("200.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            created_at=now,
        )

        model = PaymentMapper.to_model(entity)

        assert model.reference_number is None


class TestPaymentMapperRoundTrip:
    """Tests for round-trip conversion."""

    def test_entity_to_model_to_entity_preserves_data(self) -> None:
        """Test that entity -> model -> entity produces equivalent result."""
        invoice_id = InvoiceId.generate()
        payment_date = datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC)
        created_at = datetime(2024, 6, 15, 10, 35, 0, tzinfo=UTC)

        original = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=payment_date,
            payment_method="bank_transfer",
            reference_number="REF-001",
            now=created_at,
        )

        model = PaymentMapper.to_model(original)
        restored = PaymentMapper.to_entity(model)

        assert restored == original

    def test_entity_to_model_to_entity_preserves_null_reference(self) -> None:
        """Test round-trip with null reference number."""
        invoice_id = InvoiceId.generate()
        now = datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC)

        original = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("300.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            now=now,
        )

        model = PaymentMapper.to_model(original)
        restored = PaymentMapper.to_entity(model)

        assert restored == original
        assert restored.reference_number is None

    def test_model_to_entity_to_model_preserves_data(self) -> None:
        """Test that model -> entity -> model produces equivalent data."""
        model_id = uuid4()
        invoice_id = uuid4()
        payment_date = datetime(2024, 3, 20, 14, 0, 0, tzinfo=UTC)
        created_at = datetime(2024, 3, 20, 14, 5, 0, tzinfo=UTC)

        original_model = PaymentModel(
            id=model_id,
            invoice_id=invoice_id,
            amount=Decimal("1250.00"),
            payment_date=payment_date,
            payment_method="check",
            reference_number="CHK-456",
            created_at=created_at,
        )

        entity = PaymentMapper.to_entity(original_model)
        restored_model = PaymentMapper.to_model(entity)

        assert restored_model.id == original_model.id
        assert restored_model.invoice_id == original_model.invoice_id
        assert restored_model.amount == original_model.amount
        assert restored_model.payment_date == original_model.payment_date
        assert restored_model.payment_method == original_model.payment_method
        assert restored_model.reference_number == original_model.reference_number
        assert restored_model.created_at == original_model.created_at
