from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    JWT_ACCESS_SECRET: str = Field(..., min_length=32)
    JWT_REFRESH_SECRET: str = Field(..., min_length=32)

    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    APP_PORT: int = 8000

    POSTGRES_USER: str = Field(..., min_length=3)
    POSTGRES_PASSWORD: str = Field(..., min_length=3)
    POSTGRES_DB: str = Field(..., min_length=3)
    POSTGRES_HOST: str = Field(..., min_length=3)
    POSTGRES_PORT: int = 5432

    model_config = SettingsConfigDict(env_file=".env")


ENV_SETTINGS = Settings()


def is_dev() -> bool:
    return ENV_SETTINGS.ENVIRONMENT == "development"
