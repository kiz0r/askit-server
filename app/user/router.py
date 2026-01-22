from fastapi import APIRouter
from fastapi.params import Depends
from app.models.user import User
from .schemas import UserOut
from app.auth.dependencies import get_current_user

router = APIRouter(tags=["User"])


@router.get("/profile", response_model=UserOut)
async def get_user_profile(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        userId=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
    )
