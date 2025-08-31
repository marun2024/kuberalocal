import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from backend.auth.service import initialize_auth_service
from backend.core.database import async_session_maker
from backend.core.migrations import create_db_and_tables
from backend.tenants.models import TenantStatus, TenantUser
from backend.tenants.service import TenantService


async def create_tenant(name: str, subdomain: str, owner_email: str):
    print(f"Creating tenant: {name} ({subdomain})")

    # auth_service = initialize_auth_service()  # Not needed for MVP

    async with async_session_maker() as session:
        existing = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if existing:
            print(f"Error: Tenant with subdomain '{subdomain}' already exists")
            return

        tenant = await TenantService.create_tenant(
            session=session, name=name, subdomain=subdomain, status=TenantStatus.TRIAL
        )

        # Skip SuperTokens tenant creation for MVP - focus on frontend auth first
        # await auth_service.create_tenant_auth(tenant)

        # Create owner invitation
        from backend.tenants import service as tenant_service

        invitation = await tenant_service.create_invitation(
            db=session,
            tenant_id=tenant.id,
            email=owner_email,
            role="owner",
            created_by="system",
        )

        print("✓ Tenant created successfully!")
        print(f"  ID: {tenant.id}")
        print(f"  Schema: {tenant.schema_name}")
        print(f"  Status: {tenant.status}")
        print(f"  Access URL: http://{subdomain}.{settings.APP_DOMAIN}")
        print("")
        print("✓ Owner invitation created")
        print(f"  Email: {owner_email}")
        print(f"  Expires: {invitation.expires_at}")
        print(f"  Invitation URL: {settings.WEBSITE_DOMAIN}/invite/{invitation.token}")
        print("")
        print(f"Send the invitation URL to {owner_email} to complete tenant setup.")


async def list_tenants(status: str | None = None):
    async with async_session_maker() as session:
        tenant_status = TenantStatus(status) if status else None
        tenants = await TenantService.list_tenants(session, tenant_status)

        if not tenants:
            print("No tenants found")
            return

        print(f"\n{'ID':<5} {'Name':<20} {'Subdomain':<20} {'Status':<10} {'Created'}")
        print("-" * 75)

        for tenant in tenants:
            print(
                f"{tenant.id:<5} {tenant.name:<20} {tenant.subdomain:<20} {tenant.status:<10} {tenant.created_at.strftime('%Y-%m-%d')}"
            )


async def update_tenant_status(subdomain: str, status: str):
    async with async_session_maker() as session:
        tenant = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if not tenant:
            print(f"Error: Tenant with subdomain '{subdomain}' not found")
            return

        new_status = TenantStatus(status)
        updated = await TenantService.update_tenant_status(
            session=session, tenant_id=tenant.id, status=new_status, user_id="system"
        )

        if updated:
            print(f"✓ Tenant status updated to: {new_status}")
        else:
            print("Error: Failed to update tenant status")


async def delete_tenant(subdomain: str, reason: str = None):
    async with async_session_maker() as session:
        tenant = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if not tenant:
            print(f"Error: Tenant with subdomain '{subdomain}' not found")
            return

        if tenant.status == TenantStatus.PENDING_DELETION:
            print(f"Tenant '{tenant.name}' is already pending deletion")
            return

        print(f"This will mark tenant '{tenant.name}' for deletion (can be restored)")
        confirm = input("Type 'DELETE' to confirm: ")

        if confirm != "DELETE":
            print("Deletion cancelled")
            return

        result = await TenantService.soft_delete_tenant(
            session=session,
            tenant_id=tenant.id,
            user_id="system",
            deletion_reason=reason,
        )

        if result:
            print(f"✓ Tenant '{tenant.name}' marked for deletion")
            print(f"  Status: {result.status}")
            print(f"  Deleted at: {result.deleted_at}")
            print(f"  Reason: {result.deletion_reason or 'No reason provided'}")
            print(f"  Can be restored with: uv run poe tenant-restore {subdomain}")
        else:
            print("Error: Failed to delete tenant")


async def restore_tenant(subdomain: str):
    async with async_session_maker() as session:
        tenant = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if not tenant:
            print(f"Error: Tenant with subdomain '{subdomain}' not found")
            return

        if tenant.status != TenantStatus.PENDING_DELETION:
            print(
                f"Tenant '{tenant.name}' is not pending deletion (status: {tenant.status})"
            )
            return

        result = await TenantService.restore_tenant(
            session=session, tenant_id=tenant.id, user_id="system"
        )

        if result:
            print(f"✓ Tenant '{tenant.name}' restored successfully")
            print(f"  Status: {result.status}")
        else:
            print("Error: Failed to restore tenant")


async def hard_delete_tenant(subdomain: str, force: bool = False):
    auth_service = initialize_auth_service()

    async with async_session_maker() as session:
        tenant = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if not tenant:
            print(f"Error: Tenant with subdomain '{subdomain}' not found")
            return

        if not force and tenant.status != TenantStatus.PENDING_DELETION:
            print("Error: Tenant must be soft deleted first. Use --force to override.")
            print(f"Current status: {tenant.status}")
            return

        print(
            f"WARNING: This will PERMANENTLY delete tenant '{tenant.name}' and ALL data!"
        )
        print("This action CANNOT be undone!")
        confirm = input("Type 'PERMANENTLY_DELETE' to confirm: ")

        if confirm != "PERMANENTLY_DELETE":
            print("Hard deletion cancelled")
            return

        try:
            await auth_service.delete_tenant_auth(subdomain)
        except Exception:
            print("Warning: Failed to delete auth provider tenant (may not exist)")

        success = await TenantService.hard_delete_tenant(
            session=session, tenant_id=tenant.id, user_id="system", force=force
        )

        if success:
            print(f"✓ Tenant '{tenant.name}' permanently deleted")
        else:
            print("Error: Failed to hard delete tenant")


async def list_deleted_tenants(older_than_days: int = None):
    async with async_session_maker() as session:
        tenants = await TenantService.get_soft_deleted_tenants(session, older_than_days)

        if not tenants:
            age_filter = (
                f" (older than {older_than_days} days)" if older_than_days else ""
            )
            print(f"No soft deleted tenants found{age_filter}")
            return

        print(
            f"\n{'Subdomain':<20} {'Name':<25} {'Deleted At':<12} {'Days Ago':<8} {'Reason'}"
        )
        print("-" * 90)

        from backend.core.base_models import utc_now
        now = utc_now()
        for tenant in tenants:
            days_ago = (now - tenant.deleted_at).days if tenant.deleted_at else 0
            reason = tenant.deletion_reason or "No reason"
            deleted_date = (
                tenant.deleted_at.strftime("%Y-%m-%d")
                if tenant.deleted_at
                else "Unknown"
            )

            print(
                f"{tenant.subdomain:<20} {tenant.name:<25} {deleted_date:<12} {days_ago:<8} {reason}"
            )


async def add_user_to_tenant(subdomain: str, user_email: str, role: str = "member"):
    async with async_session_maker() as session:
        tenant = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if not tenant:
            print(f"Error: Tenant with subdomain '{subdomain}' not found")
            return

        # Set tenant context to work in the tenant's schema
        from backend.core.tenant_db import set_tenant_context

        await set_tenant_context(tenant.schema_name)

        # Check for existing user in the tenant schema
        existing_user = await session.execute(
            select(TenantUser).where(TenantUser.email == user_email)
        )
        if existing_user.scalar_one_or_none():
            print(f"Error: User {user_email} already exists in tenant {tenant.name}")
            return

        # Create user in tenant schema
        tenant_user = TenantUser(email=user_email, role=role, is_active=False)
        session.add(tenant_user)

        from backend.tenants import service as tenant_service

        invitation = await tenant_service.create_invitation(
            db=session,
            tenant_id=tenant.id,
            email=user_email,
            role=role,
            created_by="cli_admin",
        )

        await session.commit()

        print(f"✓ User invited to tenant '{tenant.name}'")
        print(f"  Email: {user_email}")
        print(f"  Role: {role}")
        print(
            f"  Invitation URL: http://{tenant.subdomain}.localhost:5173/invite/{invitation.token}"
        )


async def list_tenant_users(subdomain: str):
    async with async_session_maker() as session:
        tenant = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if not tenant:
            print(f"Error: Tenant with subdomain '{subdomain}' not found")
            return

        # Set tenant context to access users in tenant schema
        from backend.core.tenant_db import set_tenant_context

        await set_tenant_context(tenant.schema_name)

        users = await session.execute(select(TenantUser))
        tenant_users = users.scalars().all()

        if not tenant_users:
            print(f"No users found for tenant '{tenant.name}'")
            return

        print(f"\n👥 Users for tenant '{tenant.name}':\n")
        for user in tenant_users:
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  Active: {'Yes' if user.is_active else 'No'}")
            print(f"  Created: {user.created_at}")
            print("")


async def remove_user_from_tenant(subdomain: str, user_email: str):
    async with async_session_maker() as session:
        tenant = await TenantService.get_tenant_by_subdomain(session, subdomain)
        if not tenant:
            print(f"Error: Tenant with subdomain '{subdomain}' not found")
            return

        # Set tenant context to access users in tenant schema
        from backend.core.tenant_db import set_tenant_context

        await set_tenant_context(tenant.schema_name)

        user = await session.execute(
            select(TenantUser).where(TenantUser.email == user_email)
        )
        tenant_user = user.scalar_one_or_none()

        if not tenant_user:
            print(f"Error: User {user_email} not found in tenant {tenant.name}")
            return

        await session.delete(tenant_user)
        await session.commit()

        print(f"✓ User {user_email} removed from tenant '{tenant.name}'")


async def init_database():
    print("Initializing database...")
    await create_db_and_tables()
    print("✓ Database initialized")


if __name__ == "__main__":
    import argparse

    from backend.core.config import settings

    parser = argparse.ArgumentParser(description="Tenant Administration CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init database
    init_parser = subparsers.add_parser("init", help="Initialize database")

    # Create tenant
    create_parser = subparsers.add_parser("create", help="Create a new tenant")
    create_parser.add_argument("name", help="Tenant name")
    create_parser.add_argument("subdomain", help="Tenant subdomain")
    create_parser.add_argument("owner_email", help="Owner email address")

    # List tenants
    list_parser = subparsers.add_parser("list", help="List all tenants")
    list_parser.add_argument(
        "--status",
        help="Filter by status",
        choices=["active", "inactive", "suspended", "trial"],
    )

    # Update tenant status
    status_parser = subparsers.add_parser("status", help="Update tenant status")
    status_parser.add_argument("subdomain", help="Tenant subdomain")
    status_parser.add_argument(
        "status",
        help="New status",
        choices=["active", "inactive", "suspended", "trial"],
    )

    # Delete tenant
    delete_parser = subparsers.add_parser(
        "delete", help="Delete a tenant (can be restored)"
    )
    delete_parser.add_argument("subdomain", help="Tenant subdomain")
    delete_parser.add_argument("--reason", help="Reason for deletion")

    # Restore tenant
    restore_parser = subparsers.add_parser("restore", help="Restore a deleted tenant")
    restore_parser.add_argument("subdomain", help="Tenant subdomain")

    # Hard delete tenant
    hard_delete_parser = subparsers.add_parser(
        "hard-delete", help="Permanently delete a tenant"
    )
    hard_delete_parser.add_argument("subdomain", help="Tenant subdomain")
    hard_delete_parser.add_argument(
        "--force", action="store_true", help="Force delete without delete first"
    )

    # List deleted tenants
    list_deleted_parser = subparsers.add_parser(
        "list-deleted", help="List deleted tenants"
    )
    list_deleted_parser.add_argument(
        "--older-than", type=int, help="Show only tenants deleted more than N days ago"
    )

    # Add user to tenant
    user_parser = subparsers.add_parser("add-user", help="Add user to tenant")
    user_parser.add_argument("subdomain", help="Tenant subdomain")
    user_parser.add_argument("email", help="User email")
    user_parser.add_argument(
        "--role", default="member", help="User role (default: member)"
    )

    # List tenant users
    list_users_parser = subparsers.add_parser("list-users", help="List users in tenant")
    list_users_parser.add_argument("subdomain", help="Tenant subdomain")

    # Remove user from tenant
    remove_user_parser = subparsers.add_parser(
        "remove-user", help="Remove user from tenant"
    )
    remove_user_parser.add_argument("subdomain", help="Tenant subdomain")
    remove_user_parser.add_argument("email", help="User email")

    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(init_database())
    elif args.command == "create":
        asyncio.run(create_tenant(args.name, args.subdomain, args.owner_email))
    elif args.command == "list":
        asyncio.run(list_tenants(args.status))
    elif args.command == "status":
        asyncio.run(update_tenant_status(args.subdomain, args.status))
    elif args.command == "delete":
        asyncio.run(delete_tenant(args.subdomain, args.reason))
    elif args.command == "restore":
        asyncio.run(restore_tenant(args.subdomain))
    elif args.command == "hard-delete":
        asyncio.run(hard_delete_tenant(args.subdomain, args.force))
    elif args.command == "list-deleted":
        asyncio.run(list_deleted_tenants(args.older_than))
    elif args.command == "add-user":
        asyncio.run(add_user_to_tenant(args.subdomain, args.email, args.role))
    elif args.command == "list-users":
        asyncio.run(list_tenant_users(args.subdomain))
    elif args.command == "remove-user":
        asyncio.run(remove_user_from_tenant(args.subdomain, args.email))
    else:
        parser.print_help()
