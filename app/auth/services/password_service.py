from passlib.context import CryptContext


class PasswordService:
    """Service for handling password hashing and verification."""

    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self._pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self._pwd_context.verify(password, hashed_password)
