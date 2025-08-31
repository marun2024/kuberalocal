
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.core.base_models import utc_now
from backend.models.shared import (
    PricingPlan,
    SystemConfiguration,
    TenantSubscription,
)


class SharedService:
    """Service for managing shared models that exist in the public schema"""

    @staticmethod
    async def get_pricing_plans(
        session: AsyncSession, active_only: bool = True
    ) -> list[PricingPlan]:
        """Get all pricing plans (shared across tenants)"""
        # Always query from public schema
        statement = select(PricingPlan)
        if active_only:
            statement = statement.where(PricingPlan.is_active)

        result = await session.execute(statement)
        return result.scalars().all()

    @staticmethod
    async def get_tenant_subscription(
        session: AsyncSession, tenant_id: int
    ) -> TenantSubscription | None:
        """Get tenant's current subscription"""
        statement = (
            select(TenantSubscription)
            .where(TenantSubscription.tenant_id == tenant_id)
            .where(TenantSubscription.is_active)
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_tenant_subscription(
        session: AsyncSession,
        tenant_id: int,
        plan_id: int,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
    ) -> TenantSubscription:
        """Create or update tenant subscription"""
        # Deactivate existing subscription
        existing = await SharedService.get_tenant_subscription(session, tenant_id)
        if existing:
            existing.is_active = False

        # Create new subscription
        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            is_active=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)

        return subscription

    @staticmethod
    async def get_system_config(
        session: AsyncSession, key: str
    ) -> SystemConfiguration | None:
        """Get system configuration value"""
        statement = select(SystemConfiguration).where(SystemConfiguration.key == key)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def set_system_config(
        session: AsyncSession,
        key: str,
        value: dict,
        description: str | None = None,
        is_sensitive: bool = False,
    ) -> SystemConfiguration:
        """Set system configuration value"""
        existing = await SharedService.get_system_config(session, key)

        if existing:
            existing.value = value
            existing.description = description
            existing.is_sensitive = is_sensitive
            existing.updated_at = utc_now()
            config = existing
        else:
            config = SystemConfiguration(
                key=key,
                value=value,
                description=description,
                is_sensitive=is_sensitive,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            session.add(config)

        await session.commit()
        await session.refresh(config)

        return config


class TenantLimitsService:
    """Service for checking tenant limits based on their subscription"""

    @staticmethod
    async def check_user_limit(
        session: AsyncSession, tenant_id: int, current_users: int
    ) -> bool:
        """Check if tenant can add more users"""
        subscription = await SharedService.get_tenant_subscription(session, tenant_id)

        if not subscription:
            # No subscription = free tier limits
            return current_users < 3

        # Get plan limits
        plan = subscription.plan
        if plan.max_users is None:
            return True  # Unlimited

        return current_users < plan.max_users

    @staticmethod
    async def check_vendor_limit(
        session: AsyncSession, tenant_id: int, current_vendors: int
    ) -> bool:
        """Check if tenant can add more vendors"""
        subscription = await SharedService.get_tenant_subscription(session, tenant_id)

        if not subscription:
            # No subscription = free tier limits
            return current_vendors < 10

        # Get plan limits
        plan = subscription.plan
        if plan.max_vendors is None:
            return True  # Unlimited

        return current_vendors < plan.max_vendors
