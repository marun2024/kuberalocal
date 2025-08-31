"""
Database schema creation and migration operations.
"""

from sqlalchemy import text
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlmodel import SQLModel

from backend.core.database import engine


async def create_shared_schema():
    """
    Create/reset public schema with shared tables.
    This drops and recreates the public schema with only shared tables.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with SQLModel
        from backend.core import shared_models  # noqa: F401
        from backend.tenants import models as tenant_models  # noqa: F401
        #from backend.vendors import models as vendor_models  # noqa: F401
        from backend.contracts.models import Contract as contract_model
        from backend.contracts.models import Tag as tag_models
        #from backend.contracts.models import TagContractLink as tag_contract_link_models

        # Drop and recreate public schema
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

        # Create only shared tables (those explicitly marked with public schema)
        for table in SQLModel.metadata.tables.values():
            # Only create tables that explicitly belong to public schema
            if getattr(table, "schema", None) == "public":
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True)
                )


async def create_tenant_schema(schema_name: str):
    """
    Create/reset a tenant schema with tenant-isolated tables.

    Args:
        schema_name: The tenant schema name (e.g., 'tenant_testcompany')
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with SQLModel
        from backend.core import shared_models  # noqa: F401
        from backend.sessions import models as session_models  # noqa: F401
        from backend.tenants import models as tenant_models  # noqa: F401
        #from backend.vendors import models as vendor_models  # noqa: F401
        from backend.contracts.models import Contract as contract_models
        from backend.contracts.models import Tag as tag_models
        #from backend.contracts import TagContractLink as tag_contract_link_models

        # Drop and recreate tenant schema
        await conn.execute(DropSchema(schema_name, cascade=True, if_exists=True))
        await conn.execute(CreateSchema(schema_name))

        # Create only tenant-isolated tables (those NOT in public schema)
        # Make a list copy to avoid dictionary mutation during iteration
        tables_to_create = list(SQLModel.metadata.tables.values())

        for table in tables_to_create:
            # Skip tables that belong to public schema
            if getattr(table, "schema", None) == "public":
                continue

            # Create a copy of the table with the tenant schema
            table_copy = table.tometadata(SQLModel.metadata, schema=schema_name)
            await conn.run_sync(
                lambda sync_conn, t=table_copy: t.create(sync_conn, checkfirst=True)
            )


async def init_shared_schema():
    """
    Initialize shared tables in public schema without dropping existing data.
    Safe to run on app startup.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with SQLModel
        from backend.core import shared_models  # noqa: F401
        from backend.sessions import models as session_models  # noqa: F401
        from backend.tenants import models as tenant_models  # noqa: F401
        #from backend.vendors import models as vendor_models  # noqa: F401
        from backend.contracts import Tag as tag_models
        from backend.contracts import Contract as contract_models
        #from backend.contracts import TagContractLink as tag_contract_link_models

        # Create only shared tables (those explicitly marked with public schema)
        for table in SQLModel.metadata.tables.values():
            # Only create tables that explicitly belong to public schema
            if getattr(table, "schema", None) == "public":
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True)
                )

async def run_migration(migration_sql: str):
    """
    Run a raw SQL migration.
    Useful for complex migrations that can't be expressed via SQLModel.
    """
    async with engine.begin() as conn:
        await conn.execute(text(migration_sql))
