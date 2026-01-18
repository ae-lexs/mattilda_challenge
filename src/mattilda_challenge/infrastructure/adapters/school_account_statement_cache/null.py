from __future__ import annotations

from mattilda_challenge.application.dtos import (
    SchoolAccountStatement,
)
from mattilda_challenge.application.ports import (
    SchoolAccountStatementCache,
)
from mattilda_challenge.domain.value_objects import SchoolId


class NullSchoolAccountStatementCache(SchoolAccountStatementCache):
    """No-op cache implementation for school account statements."""

    async def get(self, school_id: SchoolId) -> SchoolAccountStatement | None:  # noqa: ARG002
        return None

    async def set(self, statement: SchoolAccountStatement) -> None:  # noqa: ARG002
        pass
