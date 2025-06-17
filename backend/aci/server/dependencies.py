from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request, Security
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
    ProjectNotFound,
)
from aci.common.logging_setup import get_logger
from aci.server import billing, config

logger = get_logger(__name__)
http_bearer = HTTPBearer(auto_error=True, description="login to receive a JWT token")
api_key_header = APIKeyHeader(
    name=config.ACI_API_KEY_HEADER,
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
        logger.error(f"API key not found, partial_api_key={api_key_key[:4]}****{api_key_key[-4:]}")
        raise InvalidAPIKey("api key not found")

    elif api_key.status == APIKeyStatus.DISABLED:
        logger.error(f"API key is disabled, api_key_id={api_key.id}")
        raise InvalidAPIKey("API key is disabled")

    elif api_key.status == APIKeyStatus.DELETED:
        logger.error(f"API key is deleted, api_key_id={api_key.id}")
        raise InvalidAPIKey("API key is deleted")

    else:
        api_key_id: UUID = api_key.id
        logger.info(f"API key validation successful, api_key_id={api_key_id}")
        return api_key_id


def validate_agent(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> Agent:
    agent = crud.projects.get_agent_by_api_key_id(db_session, api_key_id)
    if not agent:
        raise AgentNotFound(f"Agent not found, api_key_id={api_key_id}")

    return agent


# TODO: use cache (redis)
# TODO: better way to handle replace(tzinfo=datetime.timezone.utc) ?
# TODO: context return api key object instead of api_key_id
def validate_project_quota(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> Project:
    logger.debug(f"Validating project quota, api_key_id={api_key_id}")

    project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    if not project:
        logger.error(f"Project not found, api_key_id={api_key_id}")
        raise ProjectNotFound(f"Project not found, api_key_id={api_key_id}")

    now: datetime = datetime.now(UTC)
    need_reset = now >= project.daily_quota_reset_at.replace(tzinfo=UTC) + timedelta(days=1)

    if not need_reset and project.daily_quota_used >= config.PROJECT_DAILY_QUOTA:
        logger.warning(
            f"Daily quota exceeded, "
            f"project_id={project.id} "
            f"daily_quota_used={project.daily_quota_used} "
            f"daily_quota={config.PROJECT_DAILY_QUOTA}"
        )
        raise DailyQuotaExceeded(
            f"Daily quota exceeded for project={project.id}, "
            f"daily_quota_used={project.daily_quota_used} "
            f"daily quota={config.PROJECT_DAILY_QUOTA}"
        )

    crud.projects.increase_project_quota_usage(db_session, project)
    # TODO: commit here with the same db_session or should create a separate db_session?
    db_session.commit()

    logger.info(f"Project quota validation successful, project_id={project.id}")
    return project


def validate_monthly_api_quota(
    request: Request,
    db_session: Annotated[Session, Depends(yield_db_session)],
    project: Annotated[Project, Depends(validate_project_quota)],
) -> None:
    """
    Use quota for a project operation.

    1. Get subscription and quota limit
    2. Reset quota if new billing cycle has started
    3. Increment usage or raise error if exceeded
    """
    # Only check quota for app search and function search/execute endpoints
    path = request.url.path
    is_quota_limited_endpoint = path.startswith(f"{config.ROUTER_PREFIX_APPS}/search") or (
        path.startswith(f"{config.ROUTER_PREFIX_FUNCTIONS}/")
        and (path.endswith("/execute") or path.endswith("/search"))
    )
    if not is_quota_limited_endpoint:
        return

    subscription = billing.get_subscription_by_org_id(db_session, project.org_id)
    monthly_quota_limit = subscription.plan.features["api_calls_monthly"]

    billing.reset_quota_if_new_billing_cycle(db_session, project, subscription)
    billing.increment_quota(db_session, project, monthly_quota_limit)
    db_session.commit()

    logger.info("monthly api quota validation successful", extra={"project_id": project.id})


def get_request_context(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
    agent: Annotated[Agent, Depends(validate_agent)],
    project: Annotated[Project, Depends(validate_project_quota)],
    _: Annotated[None, Depends(validate_monthly_api_quota)],
) -> RequestContext:
    """
    Returns a RequestContext object containing the DB session,
    the validated API key ID, and the project ID.
    """
    logger.info(
        f"Populating request context, api_key_id={api_key_id}, "
        f"project_id={project.id}, agent_id={agent.id}"
    )
    return RequestContext(
        db_session=db_session,
        api_key_id=api_key_id,
        project=project,
        agent=agent,
    )
