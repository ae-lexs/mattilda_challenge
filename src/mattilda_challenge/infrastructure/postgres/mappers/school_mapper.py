"""Mapper between School entity and SchoolModel ORM."""

from __future__ import annotations

from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.postgres.models import SchoolModel


class SchoolMapper:
    """
    Maps between School entity and SchoolModel ORM.

    Responsibilities:
    - Convert SchoolId value object to/from raw UUID
    - Pass through string fields (name, address)
    - Pass through UTC timestamps (validated by domain)

    Stateless: All methods are static.
    """

    @staticmethod
    def to_entity(model: SchoolModel) -> School:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy SchoolModel

        Returns:
            Immutable School entity
        """
        return School(
            id=SchoolId(value=model.id),
            name=model.name,
            address=model.address,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: School) -> SchoolModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Immutable School entity

        Returns:
            Mutable SchoolModel
        """
        return SchoolModel(
            id=entity.id.value,
            name=entity.name,
            address=entity.address,
            created_at=entity.created_at,
        )
