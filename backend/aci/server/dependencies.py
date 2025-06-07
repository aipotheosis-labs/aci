from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader, HTTPBearer
from sqlalchemy.orm import Session

from aci.common import utils
from aci.common.db import crud
from aci.common.db.sql_models import Agent, Project
from aci.common.enums import APIKeyStatus
from aci.common.exceptions import (
    AgentNotFound,
    DailyQuotaExceeded,
    InvalidAPIKey,
    MonthlyQuotaExceeded,
    ProjectNotFound,
)
from aci.common.logging_setup import get_logger
from aci.server import billing, config

logger = get_logger(__name__)
http_bearer = HTTPBearer(auto_error=True, description="login to receive a JWT token")
api_key_header = APIKeyHeader(
    name=config.AIPOLABS_API_KEY_NAME,
    description="API key for authentication",
    auto_error=True,
)


class RequestContext:
    def __init__(self, db_session: Session, api_key_id: UUID, project: Project, agent: Agent):
        self.db_session = db_session
        self.api_key_id = api_key_id
        self.project = project
        self.agent = agent


def yield_db_session() -> Generator[Session, None, None]:
    db_session = utils.create_db_session(config.DB_FULL_URL)
    try:
        yield db_session
    finally:
        db_session.close()


def validate_api_key(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_key: Annotated[str, Security(api_key_header)],
) -> UUID:
    """Validate API key and return the API key ID. (not the actual API key string)"""
    api_key = crud.projects.get_api_key(db_session, api_key_key)
    if api_key is None:
        logger.error(
            "api key not found",
            extra={"partial_api_key": f"{api_key_key[:4]}****{api_key_key[-4:]}"},
        )
        raise InvalidAPIKey("api key not found")

    elif api_key.status == APIKeyStatus.DISABLED:
        logger.error("api key is disabled", extra={"api_key_id": api_key.id})
        raise InvalidAPIKey("API key is disabled")

    elif api_key.status == APIKeyStatus.DELETED:
        logger.error("api key is deleted", extra={"api_key_id": api_key.id})
        raise InvalidAPIKey("API key is deleted")

    else:
        api_key_id: UUID = api_key.id
        logger.info("api key validation successful", extra={"api_key_id": api_key_id})
        return api_key_id


def validate_agent(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> Agent:
    agent = crud.projects.get_agent_by_api_key_id(db_session, api_key_id)
    if not agent:
        raise AgentNotFound(f"agent not found for api_key_id={api_key_id}")

    return agent


# TODO: use cache (redis)
# TODO: better way to handle replace(tzinfo=datetime.timezone.utc) ?
# TODO: context return api key object instead of api_key_id
def validate_project_quota(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> Project:
    logger.debug("validating project quota", extra={"api_key_id": api_key_id})

    project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    if not project:
        logger.error("project not found", extra={"api_key_id": api_key_id})
        raise ProjectNotFound(f"project not found for api_key_id={api_key_id}")

    # Get subscription to check plan type
    subscription = billing.get_subscription_by_org_id(db_session, project.org_id)

    now: datetime = datetime.now(UTC)

    # Check if we need to reset monthly quota for free plans
    if subscription.plan.name == "free":
        # Check if we're in a new month since last reset
        last_reset = project.api_quota_last_reset.replace(tzinfo=UTC)
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_reset_month = last_reset.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if current_month > last_reset_month:
            # Reset monthly quota for all projects in the org
            crud.projects.reset_api_monthly_quota_for_org(db_session, project.org_id, now)
            db_session.commit()
            # Refresh project to get updated quota
            db_session.refresh(project)

        # Check monthly quota for free plans
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

        # Increase monthly quota usage for free plans
        crud.projects.increase_api_monthly_quota_usage(db_session, project)
    else:
        # For paid plans, use the existing daily quota logic
        need_reset = now >= project.daily_quota_reset_at.replace(tzinfo=UTC) + timedelta(days=1)

        if not need_reset and project.daily_quota_used >= config.PROJECT_DAILY_QUOTA:
            logger.warning(
                "daily quota exceeded",
                extra={
                    "project_id": project.id,
                    "daily_quota_used": project.daily_quota_used,
                    "daily_quota": config.PROJECT_DAILY_QUOTA,
                },
            )
            raise DailyQuotaExceeded(
                f"daily quota exceeded for project={project.id}, daily quota used={project.daily_quota_used}, "
                f"daily quota={config.PROJECT_DAILY_QUOTA}"
            )

        crud.projects.increase_project_quota_usage(db_session, project)

    # TODO: commit here with the same db_session or should create a separate db_session?
    db_session.commit()

    logger.info("project quota validation successful", extra={"project_id": project.id})
    return project


def get_request_context(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
    agent: Annotated[Agent, Depends(validate_agent)],
    project: Annotated[Project, Depends(validate_project_quota)],
) -> RequestContext:
    """
    Returns a RequestContext object containing the DB session,
    the validated API key ID, and the project ID.
    """
    logger.info(
        "populating request context",
        extra={"api_key_id": api_key_id, "project_id": project.id, "agent_id": agent.id},
    )
    return RequestContext(
        db_session=db_session,
        api_key_id=api_key_id,
        project=project,
        agent=agent,
    )
