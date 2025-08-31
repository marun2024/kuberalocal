"""
Core database configuration and session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.core.config import settings

# Create async engine with connection pooling disabled for multi-tenant safety
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=NullPool,  # Disable pooling for multi-tenant safety
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a basic database session.
    For tenant-aware sessions, use get_tenant_session from tenant_db module.
    """
    async with async_session_maker() as session:
        yield session




async def check_database_connection() -> bool:
    """
    Check if database is accessible.
    Useful for health checks.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
