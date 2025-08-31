from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.deps import get_public_db

router = APIRouter()


async def check_database(db: AsyncSession) -> bool:
    """Check database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get("/health")
async def health_check(
    db: Annotated[AsyncSession, Depends(get_public_db)],
    response: Response,
):
    """Extensible health check with multiple sub-checks."""
    checks = {
        "database": await check_database(db),
    }

    # Overall health is healthy only if all checks pass
    all_healthy = all(checks.values())

    if all_healthy:
        response.status_code = 200
        return "Healthy"
    else:
        response.status_code = 503
        return "Unhealthy"


@router.get("/health/detailed")
async def detailed_health_check(
    db: Annotated[AsyncSession, Depends(get_public_db)],
    response: Response,
):
    """Detailed health check showing individual component status."""
    checks = {
        "database": await check_database(db),
    }

    all_healthy = all(checks.values())
    response.status_code = 200 if all_healthy else 503

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks
    }


