from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from aci.common.db.sql_models import Plan
from aci.common.enums import StripeSubscriptionInterval, StripeSubscriptionStatus


class SubscriptionBase(BaseModel):
    org_id: UUID
    plan_id: UUID
    stripe_customer_id: str
    stripe_subscription_id: str
    status: StripeSubscriptionStatus
    interval: StripeSubscriptionInterval
    current_period_end: datetime
    cancel_at_period_end: bool


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    plan_id: UUID
    status: StripeSubscriptionStatus
    stripe_customer_id: str
    interval: StripeSubscriptionInterval
    current_period_end: datetime
    cancel_at_period_end: bool


class SubscriptionFiltered(BaseModel):
    plan: Plan
    status: StripeSubscriptionStatus


class SubscriptionPublic(BaseModel):
    plan: str
    status: StripeSubscriptionStatus


class StripeSubscriptionDetails(BaseModel):
    stripe_subscription_id: str
    stripe_customer_id: str
    status: StripeSubscriptionStatus
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
