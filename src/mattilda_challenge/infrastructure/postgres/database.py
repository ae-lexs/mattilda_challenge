from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mattilda_challenge.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get async database engine (lazy singleton).

    Engine is created on first access, not at module import time.
    This allows tests to import the module without requiring
    database configuration.

    Returns:
        SQLAlchemy async engine instance.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,  # postgresql+asyncpg://user:pass@host/db
            echo=settings.debug,  # Log SQL in debug mode
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,  # Verify connections before use
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get async session factory (lazy singleton).

    Returns:
        SQLAlchemy async session factory.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession]:
    """
    Dependency injection for async session.

    Usage in FastAPI:
        @app.post("/payments")
        async def record_payment(
            request: PaymentRequest,
            session: AsyncSession = Depends(get_session)
        ):
            async with UnitOfWork(session) as uow:
                ...

    Yields:
        AsyncSession instance
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            # Note: Commit is handled by UnitOfWork
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
