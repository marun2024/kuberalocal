"""
Session management dependencies for dependency injection.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.tenant_db import get_tenant_session
from backend.sessions.service import SessionService


async def get_session_service(
    db: Annotated[AsyncSession, Depends(get_tenant_session)]
) -> SessionService:
    """Get session service with tenant-scoped database session."""
    return SessionService(db)
