"""
Development seed script - creates test tenant with sample data.
"""

import argparse
import asyncio

from faker import Faker
from sqlalchemy import text
from sqlmodel import select

from datetime import date, timedelta

from backend.auth.jwt_auth import get_password_hash
from backend.core.database import async_session_maker
from backend.core.migrations import create_shared_schema, create_tenant_schema
from backend.tenants.models import Tenant, TenantStatus, TenantUser
#from backend.vendors.models import Vendor
#from backend.vendors.schemas import VendorCreate
from backend.contracts.models.contract import Contract
from backend.contracts.schemas.contract import ContractCreate
from backend.contracts.models.tag import Tag
from backend.contracts.schemas.tag import TagCreate
import uuid
import random



fake = Faker()


async def reset_database():
    """Reset the entire database to a clean state."""
    print("🧹 Resetting database to clean state...")

    # Create/reset public schema with shared tables
    await create_shared_schema()
    print("✅ Created public schema with shared tables")


async def create_test_tenant(subdomain: str):
    """Create a test tenant in the public schema."""
    print(f"\n🏢 Creating tenant: {subdomain}")

    async with async_session_maker() as session:
        # Check if tenant already exists
        stmt = select(Tenant).where(Tenant.subdomain == subdomain)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"   Updating existing tenant: {existing.name}")
            existing.status = TenantStatus.ACTIVE
            await session.commit()
            return existing

        # Create new tenant
        tenant = Tenant(
            name=f"{subdomain.title()} Company",
            subdomain=subdomain,
            schema_name=f"tenant_{subdomain}",
            status=TenantStatus.ACTIVE
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        print(f"✅ Created tenant: {tenant.name} (ID: {tenant.id})")
        return tenant


async def create_test_user(subdomain: str):
    """Create a test user in the tenant schema."""
    print(f"\n👤 Creating test user for {subdomain}")

    schema_name = f"tenant_{subdomain}"

    async with async_session_maker() as session:
        # Set search path to tenant schema
        await session.execute(text(f"SET search_path TO {schema_name}"))

        # Check if user exists
        stmt = select(TenantUser).where(TenantUser.email == f"{subdomain}@testco.com")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"   User already exists: {existing.email}")
            return existing

        # Create new user
        user = TenantUser(
            email=f"{subdomain}@testco.com",
            first_name=subdomain.title(),
            last_name="User",
            role="admin",
            is_owner=True,
            password_hash=get_password_hash("changeMe123!"),
            is_active=True
        )
        session.add(user)
        await session.commit()
        # Don't refresh - SQLModel has issues with tenant schema
        user.id = 1  # First user will have ID 1

        print(f"✅ Created user: {user.email}")
        return user

def _fake_contract_payload(sp_id: int | None = None) -> ContractCreate:
    """Generate a realistic fake contract payload."""
    # Start within last 2 years
    start = fake.date_between(start_date="-2y", end_date="today")
    # 75% chance to have an end date 3–24 months after start
    end = start + timedelta(days=fake.random_int(min=90, max=720)) if fake.boolean(75) else None

    return ContractCreate(
        title=fake.sentence(nb_words=3).rstrip("."),  # short, title-ish
        service_provider_id=sp_id if sp_id is not None else fake.random_int(min=1, max=10),
        reference_number=f"CN-{fake.random_number(digits=6, fix_len=True)}",
        description=fake.paragraph(nb_sentences=2),
        notes=fake.sentence(nb_words=8),
        cost=round(fake.pyfloat(left_digits=5, right_digits=2, positive=True), 2),
        start_date=start,
        end_date=end,
    )

async def create_demo_contracts(subdomain: str, count: int = 8):
    """Create demo contracts using Faker."""
    print(f"\n📄 Creating {count} demo contracts...")

    schema_name = f"tenant_{subdomain}"

    async with async_session_maker() as session:
        # Set search path to tenant schema
        await session.execute(text(f"SET search_path TO {schema_name}"))

        # Some hand-crafted examples (ensure proper types)
        demo_contracts: list[ContractCreate] = [
            ContractCreate(
                title="Acme Corporation",
                service_provider_id=1,
                reference_number="CN-000123",
                description="Master services agreement for core SaaS.",
                notes="Initial onboarding in Q1.",
                cost=34.89,
                start_date=date(2025, 1, 1),
            ),
            ContractCreate(
                title="TechSupply Inc",
                service_provider_id=2,
                reference_number="CN-000456",
                description="Hardware and accessories procurement.",
                notes="Renewal due next year.",
                cost=98.76,
                start_date=date(2025, 1, 1),
            ),
            ContractCreate(
                title="Office Depot Business",
                service_provider_id=3,
                reference_number="CN-000789",
                description="Office supplies and consumables.",
                notes="Includes toner and paper bundles.",
                cost=45.67,
                start_date=date(2025, 1, 1),
            ),
        ]

        # Add Faker-generated contracts to reach the desired count
        while len(demo_contracts) < count:
            demo_contracts.append(_fake_contract_payload())

        # Insert contracts
        created_count = 0
        for contract_data in demo_contracts:
            # Convert schema to model; optionally tweak fields before insert
            contract = Contract(**contract_data.model_dump())
            # Make the reference unique for seeding
            contract.reference_number = f"{contract.reference_number}_{uuid.uuid4()}"
            # Randomize service provider if you want more spread
            contract.service_provider_id = random.randint(1, 10)

            session.add(contract)
            created_count += 1
            print(f"  {contract.title}")

        await session.commit()
        print(f" Created {created_count} demo contracts")

async def create_demo_tags(subdomain: str):
    """Create demo tags in the tenant schema."""
    print(f"\n🏷️ Creating demo tags...")

    schema_name = f"tenant_{subdomain}"
    async with async_session_maker() as session:
        # set search path
        await session.execute(text(f"SET search_path TO {schema_name}"))

        demo_tags = [
            "Tech",
            "Finance",
            "Legal",
            "HR",
            "Operations",
            "Procurement",
            "Compliance",
            "Marketing",
            "Support",
        ]

        created_count = 0
        for tag_name in demo_tags:
            # Check if it already exists
            res = await session.execute(select(Tag).where(Tag.name == tag_name))
            if res.scalar_one_or_none():
                continue

            tag = Tag(name=tag_name, description=f"Demo tag for {tag_name}")
            session.add(tag)
            created_count += 1
            print(f"   ✅ {tag_name}")

        await session.commit()
        print(f"✅ Created {created_count} demo tags")

async def create_demo_data(subdomain: str, include_contracts: bool = True, include_tags: bool = True):
    """Create all demo data for the tenant."""
    print(f" Creating demo data for {subdomain}...")

    if include_contracts:
        await create_demo_contracts(subdomain)

    if include_tags:
        await create_demo_tags(subdomain)

async def main(tenant_name: str, reset: bool = False):
    """Main seed function."""
    print(f" Starting development seed for '{tenant_name}'")

    if reset:
        await reset_database()

    # Create test tenant in public schema
    await create_test_tenant(tenant_name)

    # Create tenant schema with tenant tables
    schema_name = f"tenant_{tenant_name}"
    print(f"\n📊 Creating tenant schema: {schema_name}")
    await create_tenant_schema(schema_name)
    print("✅ Created tenant schema with tables")

    # Create test user in tenant schema
    user = await create_test_user(tenant_name)

    # Create demo data (vendors, etc.)
    await create_demo_data(tenant_name)

    print("\n" + "="*50)
    print("✨ Seed completed successfully!")
    print("="*50)
    print("\nTest credentials:")
    print(f"  Tenant: {tenant_name}")
    print(f"  Email: {tenant_name}@testco.com")
    print("  Password: changeMe123!")
    print("\nAccess URLs:")
    print(f"  Frontend: http://{tenant_name}.localhost:5173")
    print(f"  API: http://{tenant_name}.localhost:8000/api/v1")
    print("\nDatabase info:")
    print("  Database: kubera")
    print(f"  Tenant schema: tenant_{tenant_name}")
    print(f"  User ID: {user.id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed development database with test data")
    parser.add_argument(
        "--tenant-name",
        type=str,
        default="testcompany",
        help="Developer/tenant name (default: testcompany)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset entire database before seeding"
    )
    args = parser.parse_args()

    asyncio.run(main(args.tenant_name, args.reset))
