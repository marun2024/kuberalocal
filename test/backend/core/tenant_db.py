"""
Tenant-specific database operations and context management.
"""

import re
from contextvars import ContextVar

from sqlalchemy import text

from backend.core.database import async_session_maker

# Context variable to track current tenant schema
current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)




async def set_tenant_context(schema_name: str):
    """Set the current tenant context for the async context."""
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Setting tenant context to: {schema_name}")

    current_tenant.set(schema_name)

    logger.debug(f"Tenant context set successfully: {current_tenant.get()}")


def get_current_tenant() -> str | None:
    """Get the current tenant schema from context."""
    return current_tenant.get()


async def get_tenant_session():
    """
    Get a database session with tenant context applied.
    This should be used for all tenant-specific operations.
    FAILS HARD if no tenant context is set - prevents accidental cross-tenant data access.
    Must be used as an async generator to maintain session context.
    """
    import logging

    logger = logging.getLogger(__name__)

    tenant_schema = current_tenant.get()
    logger.debug(f"Getting tenant session, current context: {tenant_schema}")

    # FAIL HARD - no tenant context means this operation should not proceed
    if not tenant_schema or tenant_schema == "public":
        raise ValueError(
            "No tenant context set - tenant operations require explicit context. "
            "Use get_public_db() for public schema operations."
        )

    # Validate schema name is exactly what we expect (tenant_<name>)
    if not re.match(r'^tenant_[a-zA-Z][a-zA-Z0-9_]*$', tenant_schema):
        raise ValueError(f"Invalid tenant schema name: {tenant_schema}")

    async with async_session_maker() as session:
        logger.debug(f"Setting search_path to tenant schema: {tenant_schema}")
        # Use PostgreSQL's quote_ident function for proper identifier quoting
        await session.execute(
            text("SELECT set_config('search_path', quote_ident(:schema_name), false)"),
            {"schema_name": tenant_schema}
        )

        logger.debug("Tenant session configured successfully")
        yield session  # Use yield instead of return to keep context alive


async def get_session_for_tenant(subdomain: str):
    """
    Context manager that yields a database session configured for a specific tenant.
    Used during login before we have full auth context.
    """
    schema_name = f"tenant_{subdomain}"

    async with async_session_maker() as session:
        # Use PostgreSQL's quote_ident for safe schema name handling
        await session.execute(
            text("SELECT set_config('search_path', quote_ident(:schema_name), false)"),
            {"schema_name": schema_name}
        )
        yield session
