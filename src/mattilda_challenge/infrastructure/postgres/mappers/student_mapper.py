"""Mapper between Student entity and StudentModel ORM."""

from __future__ import annotations

from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
from mattilda_challenge.infrastructure.postgres.models import StudentModel


class StudentMapper:
    """
    Maps between Student entity and StudentModel ORM.

    Responsibilities:
    - Convert StudentId/SchoolId value objects to/from raw UUID
    - Convert StudentStatus enum to/from string
    - Pass through string fields and timestamps

    Stateless: All methods are static.
    """

    @staticmethod
    def to_entity(model: StudentModel) -> Student:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy StudentModel

        Returns:
            Immutable Student entity
        """
        return Student(
            id=StudentId(value=model.id),
            school_id=SchoolId(value=model.school_id),
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            enrollment_date=model.enrollment_date,
            status=StudentStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Student) -> StudentModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Immutable Student entity

        Returns:
            Mutable StudentModel
        """
        return StudentModel(
            id=entity.id.value,
            school_id=entity.school_id.value,
            first_name=entity.first_name,
            last_name=entity.last_name,
            email=entity.email,
            enrollment_date=entity.enrollment_date,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
