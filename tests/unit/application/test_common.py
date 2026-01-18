"""Tests for application common types (pagination, sorting, page container)."""

from __future__ import annotations

import pytest

from mattilda_challenge.application.common import Page, PaginationParams, SortParams


class TestPaginationParamsCreation:
    """Tests for PaginationParams creation and defaults."""

    def test_create_with_defaults(self) -> None:
        """Test creating PaginationParams with default values."""
        params = PaginationParams()

        assert params.offset == 0
        assert params.limit == 20

    def test_create_with_explicit_values(self) -> None:
        """Test creating PaginationParams with explicit values."""
        params = PaginationParams(offset=50, limit=100)

        assert params.offset == 50
        assert params.limit == 100

    def test_create_with_minimum_valid_values(self) -> None:
        """Test creating PaginationParams with minimum valid values."""
        params = PaginationParams(offset=0, limit=1)

        assert params.offset == 0
        assert params.limit == 1

    def test_create_with_maximum_valid_values(self) -> None:
        """Test creating PaginationParams with maximum valid values (ADR-007)."""
        params = PaginationParams(offset=10_000, limit=200)

        assert params.offset == 10_000
        assert params.limit == 200


class TestPaginationParamsOffsetValidation:
    """Tests for PaginationParams offset validation (ADR-007 Section 2.1)."""

    def test_negative_offset_raises_error(self) -> None:
        """Test that negative offset raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PaginationParams(offset=-1, limit=20)

        assert "offset must be non-negative" in str(exc_info.value)

    def test_offset_exceeds_maximum_raises_error(self) -> None:
        """Test that offset > 10,000 raises ValueError (ADR-007 limit)."""
        with pytest.raises(ValueError) as exc_info:
            PaginationParams(offset=10_001, limit=20)

        assert "offset must not exceed 10,000" in str(exc_info.value)

    def test_offset_at_boundary_10000_succeeds(self) -> None:
        """Test that offset exactly at 10,000 is valid."""
        params = PaginationParams(offset=10_000, limit=20)

        assert params.offset == 10_000


class TestPaginationParamsLimitValidation:
    """Tests for PaginationParams limit validation (ADR-007 Section 2.1)."""

    def test_zero_limit_raises_error(self) -> None:
        """Test that limit = 0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PaginationParams(offset=0, limit=0)

        assert "limit must be at least 1" in str(exc_info.value)

    def test_negative_limit_raises_error(self) -> None:
        """Test that negative limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PaginationParams(offset=0, limit=-1)

        assert "limit must be at least 1" in str(exc_info.value)

    def test_limit_exceeds_maximum_raises_error(self) -> None:
        """Test that limit > 200 raises ValueError (ADR-007 limit)."""
        with pytest.raises(ValueError) as exc_info:
            PaginationParams(offset=0, limit=201)

        assert "limit must not exceed 200" in str(exc_info.value)

    def test_limit_at_boundary_1_succeeds(self) -> None:
        """Test that limit exactly at 1 is valid."""
        params = PaginationParams(offset=0, limit=1)

        assert params.limit == 1

    def test_limit_at_boundary_200_succeeds(self) -> None:
        """Test that limit exactly at 200 is valid."""
        params = PaginationParams(offset=0, limit=200)

        assert params.limit == 200


class TestPaginationParamsImmutability:
    """Tests for PaginationParams immutability."""

    def test_offset_cannot_be_modified(self) -> None:
        """Test that offset attribute cannot be modified."""
        params = PaginationParams(offset=10, limit=20)

        with pytest.raises(AttributeError):
            params.offset = 50  # type: ignore[misc]

    def test_limit_cannot_be_modified(self) -> None:
        """Test that limit attribute cannot be modified."""
        params = PaginationParams(offset=10, limit=20)

        with pytest.raises(AttributeError):
            params.limit = 100  # type: ignore[misc]

    def test_params_are_hashable(self) -> None:
        """Test that PaginationParams can be used in sets and as dict keys."""
        params = PaginationParams(offset=10, limit=20)

        hash_value = hash(params)
        assert isinstance(hash_value, int)

        params_set = {params}
        assert params in params_set

    def test_equal_params_are_equal(self) -> None:
        """Test that params with same values are equal."""
        params1 = PaginationParams(offset=10, limit=20)
        params2 = PaginationParams(offset=10, limit=20)

        assert params1 == params2

    def test_different_params_are_not_equal(self) -> None:
        """Test that params with different values are not equal."""
        params1 = PaginationParams(offset=10, limit=20)
        params2 = PaginationParams(offset=20, limit=20)

        assert params1 != params2


class TestSortParamsCreation:
    """Tests for SortParams creation and defaults."""

    def test_create_with_defaults(self) -> None:
        """Test creating SortParams with default values."""
        params = SortParams()

        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"

    def test_create_with_explicit_values(self) -> None:
        """Test creating SortParams with explicit values."""
        params = SortParams(sort_by="due_date", sort_order="asc")

        assert params.sort_by == "due_date"
        assert params.sort_order == "asc"

    def test_create_with_asc_order(self) -> None:
        """Test creating SortParams with ascending order."""
        params = SortParams(sort_order="asc")

        assert params.sort_order == "asc"

    def test_create_with_desc_order(self) -> None:
        """Test creating SortParams with descending order."""
        params = SortParams(sort_order="desc")

        assert params.sort_order == "desc"


class TestSortParamsValidation:
    """Tests for SortParams validation."""

    def test_invalid_sort_order_raises_error(self) -> None:
        """Test that invalid sort_order raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SortParams(sort_order="invalid")

        assert "sort_order must be 'asc' or 'desc'" in str(exc_info.value)

    def test_empty_sort_order_raises_error(self) -> None:
        """Test that empty sort_order raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SortParams(sort_order="")

        assert "sort_order must be 'asc' or 'desc'" in str(exc_info.value)

    def test_uppercase_sort_order_raises_error(self) -> None:
        """Test that uppercase sort_order raises ValueError (case-sensitive)."""
        with pytest.raises(ValueError) as exc_info:
            SortParams(sort_order="ASC")

        assert "sort_order must be 'asc' or 'desc'" in str(exc_info.value)


class TestSortParamsImmutability:
    """Tests for SortParams immutability."""

    def test_sort_by_cannot_be_modified(self) -> None:
        """Test that sort_by attribute cannot be modified."""
        params = SortParams(sort_by="created_at", sort_order="desc")

        with pytest.raises(AttributeError):
            params.sort_by = "amount"  # type: ignore[misc]

    def test_sort_order_cannot_be_modified(self) -> None:
        """Test that sort_order attribute cannot be modified."""
        params = SortParams(sort_by="created_at", sort_order="desc")

        with pytest.raises(AttributeError):
            params.sort_order = "asc"  # type: ignore[misc]

    def test_params_are_hashable(self) -> None:
        """Test that SortParams can be used in sets and as dict keys."""
        params = SortParams(sort_by="created_at", sort_order="desc")

        hash_value = hash(params)
        assert isinstance(hash_value, int)

        params_set = {params}
        assert params in params_set

    def test_equal_params_are_equal(self) -> None:
        """Test that params with same values are equal."""
        params1 = SortParams(sort_by="created_at", sort_order="desc")
        params2 = SortParams(sort_by="created_at", sort_order="desc")

        assert params1 == params2


class TestPageCreation:
    """Tests for Page[T] creation."""

    def test_create_with_items(self) -> None:
        """Test creating Page with items."""
        page: Page[str] = Page(
            items=("a", "b", "c"),
            total=10,
            offset=0,
            limit=3,
        )

        assert page.items == ("a", "b", "c")
        assert page.total == 10
        assert page.offset == 0
        assert page.limit == 3

    def test_create_with_empty_items(self) -> None:
        """Test creating Page with empty items."""
        page: Page[str] = Page(
            items=(),
            total=0,
            offset=0,
            limit=20,
        )

        assert page.items == ()
        assert page.total == 0

    def test_create_with_typed_items(self) -> None:
        """Test creating Page with typed items (integers)."""
        page: Page[int] = Page(
            items=(1, 2, 3, 4, 5),
            total=100,
            offset=0,
            limit=5,
        )

        assert page.items == (1, 2, 3, 4, 5)
        assert len(page.items) == 5


class TestPageHasMore:
    """Tests for Page.has_more property (ADR-007 Section 2.2)."""

    def test_has_more_true_when_more_items_exist(self) -> None:
        """Test has_more is True when (offset + len(items)) < total."""
        page: Page[str] = Page(
            items=("a", "b", "c"),
            total=10,
            offset=0,
            limit=3,
        )

        # 0 + 3 = 3 < 10
        assert page.has_more is True

    def test_has_more_false_on_last_page(self) -> None:
        """Test has_more is False on last page."""
        page: Page[str] = Page(
            items=("h", "i", "j"),
            total=10,
            offset=7,
            limit=3,
        )

        # 7 + 3 = 10, not < 10
        assert page.has_more is False

    def test_has_more_false_when_exactly_at_total(self) -> None:
        """Test has_more is False when offset + len(items) equals total."""
        page: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )

        # 0 + 2 = 2, not < 2
        assert page.has_more is False

    def test_has_more_false_with_empty_results(self) -> None:
        """Test has_more is False with empty results."""
        page: Page[str] = Page(
            items=(),
            total=0,
            offset=0,
            limit=20,
        )

        # 0 + 0 = 0, not < 0
        assert page.has_more is False

    def test_has_more_true_with_partial_page(self) -> None:
        """Test has_more is True with partial page that has more."""
        page: Page[str] = Page(
            items=("a",),
            total=5,
            offset=0,
            limit=1,
        )

        # 0 + 1 = 1 < 5
        assert page.has_more is True

    def test_has_more_middle_page(self) -> None:
        """Test has_more calculation for middle page."""
        page: Page[str] = Page(
            items=("d", "e", "f"),
            total=10,
            offset=3,
            limit=3,
        )

        # 3 + 3 = 6 < 10
        assert page.has_more is True

    def test_has_more_second_to_last_page(self) -> None:
        """Test has_more calculation for second to last page."""
        page: Page[str] = Page(
            items=("d", "e", "f"),
            total=9,
            offset=3,
            limit=3,
        )

        # 3 + 3 = 6 < 9
        assert page.has_more is True


class TestPageImmutability:
    """Tests for Page immutability."""

    def test_items_cannot_be_modified(self) -> None:
        """Test that items attribute cannot be modified."""
        page: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )

        with pytest.raises(AttributeError):
            page.items = ("c", "d")  # type: ignore[misc]

    def test_total_cannot_be_modified(self) -> None:
        """Test that total attribute cannot be modified."""
        page: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )

        with pytest.raises(AttributeError):
            page.total = 100  # type: ignore[misc]

    def test_offset_cannot_be_modified(self) -> None:
        """Test that offset attribute cannot be modified."""
        page: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )

        with pytest.raises(AttributeError):
            page.offset = 50  # type: ignore[misc]

    def test_limit_cannot_be_modified(self) -> None:
        """Test that limit attribute cannot be modified."""
        page: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )

        with pytest.raises(AttributeError):
            page.limit = 100  # type: ignore[misc]

    def test_items_tuple_is_immutable(self) -> None:
        """Test that items tuple cannot be modified in place."""
        page: Page[list[str]] = Page(
            items=(["a"], ["b"]),
            total=2,
            offset=0,
            limit=10,
        )

        # Tuple itself is immutable
        with pytest.raises(TypeError):
            page.items[0] = ["c"]  # type: ignore[index]

    def test_page_is_hashable(self) -> None:
        """Test that Page can be used in sets and as dict keys."""
        page: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )

        hash_value = hash(page)
        assert isinstance(hash_value, int)

        page_set = {page}
        assert page in page_set

    def test_equal_pages_are_equal(self) -> None:
        """Test that pages with same values are equal."""
        page1: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )
        page2: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )

        assert page1 == page2

    def test_different_pages_are_not_equal(self) -> None:
        """Test that pages with different values are not equal."""
        page1: Page[str] = Page(
            items=("a", "b"),
            total=2,
            offset=0,
            limit=10,
        )
        page2: Page[str] = Page(
            items=("c", "d"),
            total=2,
            offset=0,
            limit=10,
        )

        assert page1 != page2
