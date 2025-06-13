from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Project
from aci.common.enums import StripeSubscriptionStatus
from aci.common.exceptions import MonthlyQuotaExceeded, SubscriptionPlanNotFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.subscription import SubscriptionFiltered

logger = get_logger(__name__)


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


def check_if_reset_is_needed(subscription: SubscriptionFiltered, project: Project) -> bool:
    """
    Check if quota reset is needed based on billing cycle.

    Returns True if a new billing cycle has started since the last reset.
    """
    last_reset = project.api_quota_last_reset.replace(tzinfo=UTC)
    current_period_start = subscription.current_period_start

    # Reset is needed if the current billing period started after our last reset
    return current_period_start > last_reset


def reset_quota_if_new_billing_cycle(
    db_session: Session, project: Project, subscription: SubscriptionFiltered
) -> None:
    """
    Reset quota if a new billing cycle has started.

    This happens when:
    - For free plans: A new month has started (1st of the month)
    - For paid plans: Stripe has started a new billing period (current_period_start updated)
    """
    # Guard: early return if no reset is needed
    if not check_if_reset_is_needed(subscription, project):
        return

    logger.info(
        "resetting monthly quota",
    )

    crud.projects.reset_api_monthly_quota_for_org(
        db_session, project.org_id, subscription.current_period_start
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
