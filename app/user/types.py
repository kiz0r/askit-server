from typing import NewType
from uuid import UUID
from pydantic import AfterValidator
from typing import Annotated


def _validate_uuid(value: str | UUID) -> str:
    """Validate and convert UUID to string format."""
    if isinstance(value, UUID):
        return str(value)
    try:
        UUID(value)
        return value
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid UUID format: {value}") from e


# Branded type for User IDs - provides compile-time type safety
UserId = NewType("UserId", str)

# Pydantic-compatible version with validation (use in schemas)
ValidatedUserId = Annotated[str, AfterValidator(_validate_uuid)]
