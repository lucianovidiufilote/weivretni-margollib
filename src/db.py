"""Database utilities."""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings

_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(AsyncAttrs, DeclarativeBase):
    """Declarative base that enables async ORM helpers."""

    metadata = MetaData(naming_convention=_NAMING_CONVENTION)


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for acquiring an async session."""

    async with async_session_factory() as session:
        yield session


async def init_models() -> None:
    """Create database tables if they do not exist."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
