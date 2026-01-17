from __future__ import annotations

from datetime import UTC, datetime

from mattilda_challenge.domain.exceptions import InvalidTimestampError


def validate_utc_timestamp(dt: datetime, field_name: str) -> None:
    """
    Validate that datetime has UTC timezone.

    **Hard invariant**: All datetimes in the domain MUST have UTC timezone.
    See ADR-003 (Time Provider) for complete policy.

    Args:
        dt: Datetime to validate
        field_name: Field name for error message

    Raises:
        InvalidTimestampError: If datetime is naive or non-UTC

    Example:
        >>> validate_utc_timestamp(datetime.now(UTC), "created_at")  # OK
        >>> validate_utc_timestamp(datetime.now(), "created_at")  # Raises
    """
    if dt.tzinfo is None:
        raise InvalidTimestampError(
            f"{field_name} must be timezone-aware, got naive datetime: {dt}"
        )

    if dt.tzinfo != UTC:
        raise InvalidTimestampError(
            f"{field_name} must have UTC timezone, got {dt.tzinfo}: {dt}"
        )
