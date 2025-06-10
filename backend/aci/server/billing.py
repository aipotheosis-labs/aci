from datetime import UTC, datetime
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
            current_period_start=datetime.now(UTC).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ),  # For the free plan, the current period start is the first day of the month
            status=StripeSubscriptionStatus.ACTIVE,
        )

    # Get the plan from the subscription
    plan = crud.plans.get_by_id(db_session, subscription.plan_id)
    if not plan:
        raise SubscriptionPlanNotFound(f"Plan {subscription.plan_id} not found")
    return SubscriptionFiltered(
        plan=plan,
        current_period_start=subscription.current_period_start,
        status=subscription.status,
    )


def reset_quota_if_period_changed(
    db_session: Session, project: Project, subscription: SubscriptionFiltered
) -> None:
    """Reset quota if billing period has changed."""
    last_reset = project.api_quota_last_reset.replace(tzinfo=UTC)
    current_period_start = subscription.current_period_start.replace(tzinfo=UTC)

    if current_period_start > last_reset:
        logger.info(
            "resetting monthly quota due to billing period change",
            extra={
                "project_id": project.id,
                "org_id": project.org_id,
                "reset_time": current_period_start,
            },
        )
        crud.projects.reset_api_monthly_quota_for_org(
            db_session, project.org_id, current_period_start
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


def increment_quota_or_reset_limit(db_session: Session, project: Project) -> None:
    """
    Use quota for a project operation.

    1. Get subscription and quota limit
    2. Reset quota if billing period changed
    3. Increment usage or raise error if exceeded
    """
    subscription = get_subscription_by_org_id(db_session, project.org_id)
    monthly_quota_limit = subscription.plan.features["api_calls_monthly"]

    reset_quota_if_period_changed(db_session, project, subscription)
    increment_quota(db_session, project, monthly_quota_limit)
    db_session.commit()
