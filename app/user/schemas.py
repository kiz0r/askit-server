from pydantic import BaseModel, EmailStr, field_validator
from app.auth.validators import AuthValidators
from .types import UserId


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        return AuthValidators.validate_username(v)

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        return AuthValidators.validate_password(v)


class UserOut(BaseModel):
    userId: UserId
    username: str
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str
