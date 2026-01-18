from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PaginationParams:
    """
    Pagination parameters for list queries.

    Immutable value object. Validated at construction.
    """

    offset: int = 0
    limit: int = 20

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise ValueError("offset must be non-negative")
        if self.offset > 10_000:
            raise ValueError("offset must not exceed 10,000")
        if self.limit < 1:
            raise ValueError("limit must be at least 1")
        if self.limit > 200:
            raise ValueError("limit must not exceed 200")


@dataclass(frozen=True, slots=True)
class SortParams:
    """
    Sorting parameters for list queries.

    Immutable value object. Valid fields checked by use case.
    """

    sort_by: str = "created_at"
    sort_order: str = "desc"  # "asc" or "desc"

    def __post_init__(self) -> None:
        if self.sort_order not in ("asc", "desc"):
            raise ValueError("sort_order must be 'asc' or 'desc'")


@dataclass(frozen=True, slots=True)
class Page[T]:
    """
    Paginated result container.

    Generic over item type. Immutable.

    Note: Page[T] is a domain-agnostic application type, not a REST concern.
    It lives in the application layer and is mapped to REST DTOs at the boundary.
    """

    items: tuple[T, ...]  # Tuple for immutability
    total: int
    offset: int
    limit: int

    @property
    def has_more(self) -> bool:
        """True if more items exist beyond current page."""
        return (self.offset + len(self.items)) < self.total
