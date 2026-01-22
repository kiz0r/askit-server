from pydantic import BaseModel, EmailStr, field_validator
from app.auth.validators import AuthValidators


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    def username_valid(self, v):
        return AuthValidators.validate_username(v)

    @field_validator("password")
    def password_valid(self, v):
        return AuthValidators.validate_password(v)


class UserOut(BaseModel):
    userId: str
    username: str
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str
