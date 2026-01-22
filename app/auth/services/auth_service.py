from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from .jwt_service import jwt_service
from .password_service import PasswordService
from app.user.services.user_service import UserService
from app.auth.exceptions import InvalidCredentialsError, UserInactiveError

password_service = PasswordService()


class AuthService:
    @staticmethod
    async def login(db: AsyncSession, email: EmailStr, password: str):
        user = await UserService.get_user_by_email(db, email)

        if user is None or not password_service.verify_password(
            password, user.password_hash
        ):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserInactiveError()

        # Update last login timestamp
        await UserService.update_last_login(db, user)

        access_token = jwt_service.create_access_token(str(user.id))
        refresh_token = jwt_service.create_refresh_token(str(user.id))

        return user, access_token, refresh_token
