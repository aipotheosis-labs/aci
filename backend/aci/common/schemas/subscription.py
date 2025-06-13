from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, PrivateAttr

from aci.common.db.sql_models import Plan
from aci.common.enums import StripeSubscriptionInterval, StripeSubscriptionStatus


class SubscriptionBase(BaseModel):
    org_id: UUID
    plan_id: UUID
    stripe_customer_id: str
    stripe_subscription_id: str
    status: StripeSubscriptionStatus
    interval: StripeSubscriptionInterval
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    plan_id: UUID
    status: StripeSubscriptionStatus
    stripe_customer_id: str
    interval: StripeSubscriptionInterval
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool


class SubscriptionFiltered(BaseModel):
    plan: Plan
    status: StripeSubscriptionStatus
    _stripe_current_period_start: datetime | None = PrivateAttr(
        default=None
    )  # Private field to store Stripe data

    @property
    def current_period_start(self) -> datetime:
        """
        Get the current period start date.

        - Free plans: 1st of current month at 00:00:00 UTC (calculated dynamically)
        - Paid plans: Use the stored current_period_start from Stripe
        """
        if self.plan.name == "free" or self._stripe_current_period_start is None:
            # For free plans, always calculate the current month's start
            return datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # For paid plans, use the actual Stripe billing period
            return self._stripe_current_period_start.replace(tzinfo=UTC)


class SubscriptionPublic(BaseModel):
    plan: str
    status: StripeSubscriptionStatus


class StripeSubscriptionDetails(BaseModel):
    stripe_subscription_id: str
    stripe_customer_id: str
    status: StripeSubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    stripe_price_id: str
    interval: StripeSubscriptionInterval


class StripeSubscriptionMetadata(BaseModel):
    org_id: UUID
    checkout_user_id: str
    checkout_user_email: str


class StripeCheckoutSessionCreate(BaseModel):
    plan_name: str
    interval: StripeSubscriptionInterval
