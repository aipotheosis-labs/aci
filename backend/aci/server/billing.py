from uuid import UUID

from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Plan, Project
from aci.common.exceptions import MonthlyQuotaExceeded, SubscriptionPlanNotFound
from aci.common.logging_setup import get_logger

logger = get_logger(__name__)


def get_active_plan_by_org_id(db_session: Session, org_id: UUID) -> Plan:
    subscription = crud.subscriptions.get_subscription_by_org_id(db_session, org_id)
    if not subscription:
        active_plan = crud.plans.get_by_name(db_session, "free")
    else:
        active_plan = crud.plans.get_by_id(db_session, subscription.plan_id)

    if not active_plan:
        raise SubscriptionPlanNotFound("Plan not found")
    return active_plan


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
