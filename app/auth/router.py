from fastapi import Request, Response, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.services.auth_service import auth_service
from app.settings import is_dev
from app.user.schemas import UserCreate, UserLogin, UserOut
from app.user.services.user_service import user_service
from app.auth.services.jwt_service import jwt_service
from app.database import get_async_db
from app.auth.exceptions import UserAlreadyExistsError, RefreshTokenMissingError

router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=UserOut)
async def register(
    user: UserCreate, response: Response, db: AsyncSession = Depends(get_async_db)
) -> UserOut:
    found_user = await user_service.get_user_by_email(db, user.email)
    if found_user is not None:
        raise UserAlreadyExistsError()

    created_user = await user_service.create_user(
        db, user.username, user.email, user.password
    )

    # Create JWT tokens immediately
    access_token = jwt_service.create_access_token(str(created_user.id))
    refresh_token = jwt_service.create_refresh_token(str(created_user.id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=not is_dev(),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=not is_dev(),
    )

    return user_service.user_to_response(created_user)


@router.post("/login", response_model=UserOut)
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
) -> UserOut:
    user, access_token, refresh_token = await auth_service.login(
        db, data.email, data.password
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=not is_dev(),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=not is_dev(),
    )

    return user_service.user_to_response(user)


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise RefreshTokenMissingError()

    payload = jwt_service.verify_refresh_token(refresh_token)
    user_id = payload["sub"]

    access_token = jwt_service.create_access_token(str(user_id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=not is_dev(),
    )

    return {"message": "OK"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "OK"}
