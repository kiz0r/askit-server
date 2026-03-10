"""
Example of using structured logging in your services.

When you need to add logging to your services, import and use the logger:
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


# Example 1: Simple info log
def example_info() -> None:
    logger.info("user_created", user_id="123", username="john_doe")
    # Output: {"event": "user_created", "user_id": "123", "username": "john_doe", ...}


# Example 2: Warning with context
def example_warning() -> None:
    logger.warning(
        "quiz_limit_reached",
        user_id="456",
        current_count=10,
        max_allowed=10,
    )


# Example 3: Error with exception
def example_error() -> None:
    try:
        # Some operation
        raise ValueError("Invalid quiz format")
    except Exception as e:
        logger.error(
            "quiz_creation_failed",
            exc_info=e,  # Includes full traceback
            user_id="789",
            quiz_data={"title": "My Quiz"},
        )


# Example 4: Debug logs (only shown when LOG_LEVEL=DEBUG)
def example_debug() -> None:
    logger.debug(
        "database_query_executed",
        query="SELECT * FROM users",
        duration_ms=45.2,
    )


# All logs automatically include:
# - timestamp
# - log_level
# - request_id (if called during a request)
# - method and path (if called during a request)
# - app="askit-server"
