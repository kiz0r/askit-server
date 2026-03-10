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


# Branded types for Quiz-related IDs - provide compile-time type safety
QuizId = NewType("QuizId", str)
QuestionId = NewType("QuestionId", str)
AnswerId = NewType("AnswerId", str)
SessionId = NewType("SessionId", str)

# Pydantic-compatible versions with validation (use in schemas)
ValidatedQuizId = Annotated[str, AfterValidator(_validate_uuid)]
ValidatedQuestionId = Annotated[str, AfterValidator(_validate_uuid)]
ValidatedAnswerId = Annotated[str, AfterValidator(_validate_uuid)]
ValidatedSessionId = Annotated[str, AfterValidator(_validate_uuid)]
