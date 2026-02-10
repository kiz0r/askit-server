from passlib.context import CryptContext
from attrs import frozen, Factory


@frozen
class PasswordService:
    """
    Immutable service for password hashing and verification.
    Uses Argon2 algorithm for secure password storage.
    """

    _pwd_context: CryptContext = Factory(
        lambda: CryptContext(schemes=["argon2"], deprecated="auto")
    )

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self._pwd_context.verify(password, hashed_password)


# Singleton instance
password_service = PasswordService()
