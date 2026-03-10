from datetime import datetime, timezone
from typing import cast
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from attrs import frozen
from app.models.user import User
from app.auth.services.password_service import password_service
from app.auth.exceptions import UserAlreadyExistsError, UsernameAlreadyExistsError
from app.user.types import UserId
from app.user.schemas import UserOut


@frozen
class UserService:
    """
    Immutable service for user-related business logic.
    Stateless service - all methods operate on provided dependencies.
    """

    def _to_user_id(self, value: str | UUID) -> UserId:
        """
        Convert UUID to UserId branded type.
        Private method for internal service use only.
        """
        if isinstance(value, UUID):
            return UserId(str(value))
        return UserId(value)

    def _from_user_id(self, user_id: UserId) -> UUID:
        """
        Convert UserId branded type to UUID for database operations.
        Private method for internal service use only.
        """
        return UUID(user_id)

    def user_to_response(self, user: User) -> UserOut:
        """
        Convert User model to UserOut response schema.
        Public method for use in routers and other services.
        """
        return UserOut(
            userId=self._to_user_id(user.id),
            username=user.username,
            email=user.email,
        )

    async def create_user(
        self, db: AsyncSession, username: str, email: EmailStr, password: str
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_service.hash_password(password),
        )
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError as e:
            await db.rollback()
            # Check if it's email or username conflict
            error_msg = str(e.orig).lower()
            if "email" in error_msg:
                raise UserAlreadyExistsError()
            elif "username" in error_msg:
                raise UsernameAlreadyExistsError()
            else:
                raise UserAlreadyExistsError()

    async def get_user_by_email(self, db: AsyncSession, email: EmailStr) -> User | None:
        user = await db.execute(select(User).where(User.email == email))
        return cast(User | None, user.scalars().first())

    async def get_user_by_id(self, db: AsyncSession, user_id: UserId) -> User | None:
        uuid_val = self._from_user_id(user_id)
        return cast(User | None, await db.get(User, uuid_val))

    async def update_last_login(self, db: AsyncSession, user: User) -> None:
        user.last_login = datetime.now(timezone.utc)
        await db.commit()


# Singleton instance
user_service = UserService()
