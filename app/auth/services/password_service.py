from passlib.context import CryptContext


class PasswordService:
    _pwd_context = CryptContext(
        schemes=["argon2"],
        deprecated="auto",
    )

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self._pwd_context.verify(password, hashed_password)
