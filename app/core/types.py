"""
DEPRECATED: This module has been refactored.

Branded types have been moved to their respective domain modules:
- UserId -> app.user.types
- QuizId, QuestionId, AnswerId, SessionId -> app.quiz.types

For backward compatibility, types are re-exported here, but direct imports
from domain modules are preferred.

DO NOT ADD NEW TYPES HERE. Add them to the appropriate domain module instead.
"""

# Re-exports for backward compatibility (DEPRECATED)
from app.user.types import UserId, ValidatedUserId
from app.quiz.types import (
    QuizId,
    QuestionId,
    AnswerId,
    SessionId,
    ValidatedQuizId,
    ValidatedQuestionId,
    ValidatedAnswerId,
    ValidatedSessionId,
)

__all__ = [
    # User types
    "UserId",
    "ValidatedUserId",
    # Quiz types
    "QuizId",
    "QuestionId",
    "AnswerId",
    "SessionId",
    "ValidatedQuizId",
    "ValidatedQuestionId",
    "ValidatedAnswerId",
    "ValidatedSessionId",
]

