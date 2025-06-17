from uuid import UUID

from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Plan, Project, Subscription
from aci.common.enums import StripeSubscriptionStatus
from aci.common.exceptions import MonthlyQuotaExceeded, SubscriptionPlanNotFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.subscription import SubscriptionPublic

logger = get_logger(__name__)


def get_subscription_and_plan_by_org_id(
    db_session: Session, org_id: UUID
) -> tuple[Subscription | None, Plan]:
    subscription = crud.subscriptions.get_subscription_by_org_id(db_session, org_id)
    plan = None
    if not subscription:
        plan = crud.plans.get_by_name(db_session, "free")
    else:
        plan = crud.plans.get_by_id(db_session, subscription.plan_id)

    if not plan:
        raise SubscriptionPlanNotFound("Plan not found")
    return subscription, plan


def get_active_plan_by_org_id(db_session: Session, org_id: UUID) -> Plan:
    subscription = crud.subscriptions.get_subscription_by_org_id(db_session, org_id)
    if not subscription:
        active_plan = crud.plans.get_by_name(db_session, "free")
    else:
        active_plan = crud.plans.get_by_id(db_session, subscription.plan_id)
    if not active_plan:
        raise SubscriptionPlanNotFound("Plan not found")
    return active_plan


def get_subscription_by_org_id(db_session: Session, org_id: UUID) -> SubscriptionPublic:
    subscription = crud.subscriptions.get_subscription_by_org_id(db_session, org_id)
    if not subscription:
        # If no subscription found, use the free plan
        plan = crud.plans.get_by_name(db_session, "free")
        if not plan:
            raise SubscriptionPlanNotFound("Free plan not found")
        return SubscriptionPublic(
            plan=plan.name,
            status=StripeSubscriptionStatus.ACTIVE,
        )

    # Get the plan from the subscription
    plan = crud.plans.get_by_id(db_session, subscription.plan_id)
    if not plan:
        raise SubscriptionPlanNotFound(f"Plan {subscription.plan_id} not found")
    return SubscriptionPublic(
        plan=plan.name,
        status=subscription.status,
    )


def increment_quota(db_session: Session, project: Project, monthly_quota_limit: int) -> None:
    """Increment quota usage or raise error if limit exceeded."""
    success = crud.projects.increment_api_monthly_quota_usage(
        db_session, project, monthly_quota_limit
    )

    if not success:
        total_monthly_usage = crud.projects.get_total_monthly_quota_usage_for_org(
            db_session, project.org_id
        )

        logger.warning(
            "monthly quota exceeded",
            extra={
                "project_id": project.id,
                "org_id": project.org_id,
                "total_monthly_usage": total_monthly_usage,
                "monthly_quota_limit": monthly_quota_limit,
            },
        )
        raise MonthlyQuotaExceeded(
            f"monthly quota exceeded for org={project.org_id}, "
            f"usage={total_monthly_usage}, limit={monthly_quota_limit}"
        )
