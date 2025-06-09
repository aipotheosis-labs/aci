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
            ),
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


def increase_quota_usage(db_session: Session, project: Project) -> None:
    """
    Common function to handle quota increases with monthly quota reset logic for both free and paid plans.

    Args:
        db_session: Database session
        project: Project object

    Raises:
        MonthlyQuotaExceeded: If monthly quota is exceeded
    """
    now: datetime = datetime.now(UTC)

    # Get subscription to check plan type
    subscription = get_subscription_by_org_id(db_session, project.org_id)

    # Handle quota reset based on plan type
    _handle_quota_reset(db_session, project, subscription, now)

    # Check monthly quota limits
    _check_monthly_quota_limit(db_session, project, subscription)

    # Increase monthly quota usage
    crud.projects.increment_api_monthly_quota_usage(db_session, project)


def _handle_quota_reset(
    db_session: Session, project: Project, subscription: SubscriptionFiltered, now: datetime
) -> None:
    """Handle quota reset logic for both free and paid plans."""
    last_reset = project.api_quota_last_reset.replace(tzinfo=UTC)
    current_period_start = subscription.current_period_start.replace(tzinfo=UTC)

    if current_period_start > last_reset:
        _reset_monthly_quota(db_session, project, current_period_start, "billing period reset")


def _reset_monthly_quota(
    db_session: Session, project: Project, reset_time: datetime, reason: str
) -> None:
    """Reset monthly quota for all projects in the org."""
    logger.info(
        f"resetting monthly quota due to {reason}",
        extra={
            "project_id": project.id,
            "org_id": project.org_id,
            "reset_time": reset_time,
        },
    )
    crud.projects.reset_api_monthly_quota_for_org(db_session, project.org_id, reset_time)


def _check_monthly_quota_limit(
    db_session: Session, project: Project, subscription: SubscriptionFiltered
) -> None:
    """Check if monthly quota limit is exceeded and raise exception if so."""
    monthly_quota_limit = subscription.plan.features["api_calls_monthly"]

    # Aggregate monthly usage across all projects in the org
    total_monthly_usage = crud.projects.get_total_monthly_quota_usage_for_org(
        db_session, project.org_id
    )

    if total_monthly_usage >= monthly_quota_limit:
        logger.warning(
            "monthly quota exceeded",
            extra={
                "project_id": project.id,
                "org_id": project.org_id,
                "total_monthly_usage": total_monthly_usage,
                "monthly_quota_limit": monthly_quota_limit,
                "plan": subscription.plan.name,
            },
        )
        raise MonthlyQuotaExceeded(
            f"monthly quota exceeded for org={project.org_id}, total monthly usage={total_monthly_usage}, "
            f"monthly quota limit={monthly_quota_limit}"
        )
