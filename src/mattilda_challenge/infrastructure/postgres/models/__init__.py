"""Postgres models."""

from mattilda_challenge.infrastructure.postgres.models.base import Base
from mattilda_challenge.infrastructure.postgres.models.school import SchoolModel
from mattilda_challenge.infrastructure.postgres.models.student import StudentModel

__all__ = [
    "Base",
    "SchoolModel",
    "StudentModel",
]
