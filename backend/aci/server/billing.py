from uuid import UUID

from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.enums import StripeSubscriptionStatus
from aci.common.exceptions import SubscriptionPlanNotFound
from aci.common.schemas.subscription import SubscriptionFiltered


def get_subscription_by_org_id(db_session: Session, org_id: UUID) -> SubscriptionFiltered:
    subscription = crud.subscriptions.get_subscription_by_org_id(db_session, org_id)
    if not subscription:
        # If no subscription found, use the free plan
        plan = crud.plans.get_by_name(db_session, "free")
        if not plan:
            raise SubscriptionPlanNotFound("Free plan not found")
        return SubscriptionFiltered(
            plan=plan,
            status=StripeSubscriptionStatus.ACTIVE,
        )

    # Get the plan from the subscription
    plan = crud.plans.get_by_id(db_session, subscription.plan_id)
    if not plan:
        raise SubscriptionPlanNotFound(f"Plan {subscription.plan_id} not found")
    return SubscriptionFiltered(
        plan=plan,
        status=subscription.status,
    )
