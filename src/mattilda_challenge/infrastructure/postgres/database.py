from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mattilda_challenge.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,  # postgresql+asyncpg://user:pass@host/db
    echo=settings.debug,  # Log SQL in debug mode
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


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
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Note: Commit is handled by UnitOfWork
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
