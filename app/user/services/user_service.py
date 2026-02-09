from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from app.models.user import User
from app.auth.services.password_service import PasswordService
from app.auth.exceptions import UserAlreadyExistsError, UsernameAlreadyExistsError
from app.core.types import UserId

password_service = PasswordService()


class UserService:
    @staticmethod
    async def create_user(
        db: AsyncSession, username: str, email: EmailStr, password: str
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

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: EmailStr) -> User | None:
        user = await db.execute(select(User).where(User.email == email))
        return user.scalars().first()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UserId) -> User | None:
        return await db.get(User, user_id)

    @staticmethod
    async def update_last_login(db: AsyncSession, user: User) -> None:
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
