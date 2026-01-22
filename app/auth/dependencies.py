from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.user.services.user_service import UserService
from app.auth.services.jwt_service import jwt_service
from app.auth.exceptions import NotAuthenticatedError, UserInactiveError


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    token = request.cookies.get("access_token")
    if not token:
        raise NotAuthenticatedError()

    payload = jwt_service.verify_access_token(token)
    user_id = payload["sub"]
    user = await UserService.get_user_by_id(db, user_id)

    if not user:
        raise NotAuthenticatedError()

    if not user.is_active:
        raise UserInactiveError()

    return user
