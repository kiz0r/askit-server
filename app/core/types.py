"""
Branded types for type-safe ID handling.

Similar to TypeScript's branded types, these provide compile-time type safety
to prevent accidentally passing a UserId where a QuizId is expected.

Usage:
    from app.core.types import UserId, QuizId, QuestionId, AnswerId

    def get_user(user_id: UserId) -> User: ...
    def get_quiz(quiz_id: QuizId) -> Quiz: ...

    # Type checker will catch this mistake:
    # get_user(quiz_id)  # Error: QuizId is not UserId
"""

from typing import Annotated, NewType
from uuid import UUID
from pydantic import AfterValidator, PlainSerializer


def _validate_uuid(value: str | UUID) -> str:
    """Validate and convert UUID to string format."""
    if isinstance(value, UUID):
        return str(value)
    try:
        # Validate it's a proper UUID format
        UUID(value)
        return value
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid UUID format: {value}") from e


# Base branded UUID type with validation
BrandedUUID = Annotated[
    str,
    AfterValidator(_validate_uuid),
    PlainSerializer(lambda x: str(x), return_type=str),
]

# Branded ID types - these are distinct types for type checking
# Using NewType for compile-time type safety
UserId = NewType("UserId", str)
QuizId = NewType("QuizId", str)
QuestionId = NewType("QuestionId", str)
AnswerId = NewType("AnswerId", str)
SessionId = NewType("SessionId", str)

# Pydantic-compatible versions with validation (use in schemas)
ValidatedUserId = Annotated[str, AfterValidator(_validate_uuid)]
ValidatedQuizId = Annotated[str, AfterValidator(_validate_uuid)]
ValidatedQuestionId = Annotated[str, AfterValidator(_validate_uuid)]
ValidatedAnswerId = Annotated[str, AfterValidator(_validate_uuid)]
ValidatedSessionId = Annotated[str, AfterValidator(_validate_uuid)]


def to_user_id(value: str | UUID) -> UserId:
    """Convert a string or UUID to a UserId."""
    return UserId(_validate_uuid(value))


def to_quiz_id(value: str | UUID) -> QuizId:
    """Convert a string or UUID to a QuizId."""
    return QuizId(_validate_uuid(value))


def to_question_id(value: str | UUID) -> QuestionId:
    """Convert a string or UUID to a QuestionId."""
    return QuestionId(_validate_uuid(value))


def to_answer_id(value: str | UUID) -> AnswerId:
    """Convert a string or UUID to an AnswerId."""
    return AnswerId(_validate_uuid(value))


def to_session_id(value: str | UUID) -> SessionId:
    """Convert a string or UUID to a SessionId."""
    return SessionId(_validate_uuid(value))
