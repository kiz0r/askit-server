from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from app.settings import ENV_SETTINGS

DATABASE_URL = f"postgresql+asyncpg://{ENV_SETTINGS.POSTGRES_USER}:{ENV_SETTINGS.POSTGRES_PASSWORD}@{ENV_SETTINGS.POSTGRES_HOST}:{ENV_SETTINGS.POSTGRES_PORT}/{ENV_SETTINGS.POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def init_db() -> None:
    """Async tables creation"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
