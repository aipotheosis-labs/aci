from datetime import datetime, timedelta, timezone
from typing import Annotated, Generator
from uuid import UUID

from authlib.jose import JoseError, jwt
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Project, User
from aipolabs.common.enums import APIKeyStatus
from aipolabs.common.exceptions import (
    DailyQuotaExceeded,
    InvalidAPIKey,
    InvalidBearerToken,
    ProjectNotFound,
    UserNotFound,
)
from aipolabs.common.logging import get_logger
from aipolabs.server import config

logger = get_logger(__name__)
http_bearer = HTTPBearer(auto_error=True, description="login to receive a JWT token")
api_key_header = APIKeyHeader(
    name=config.AOPOLABS_API_KEY_NAME,
    description="API key for authentication",
    auto_error=True,
)


class RequestContext:
    def __init__(self, db_session: Session, api_key_id: UUID, project: Project):
        self.db_session = db_session
        self.api_key_id = api_key_id
        self.project = project


def yield_db_session() -> Generator[Session, None, None]:
    db_session = utils.create_db_session(config.DB_FULL_URL)
    try:
        yield db_session
    finally:
        db_session.close()


# TODO: rate limit and quota check for http bearer token and relevant routes
def validate_http_bearer(
    db_session: Annotated[Session, Depends(yield_db_session)],
    auth_data: Annotated[HTTPAuthorizationCredentials, Security(http_bearer)],
) -> User:
    """
    Validate HTTP Bearer token and return user ID.
    HTTP Bearer token is generated after a user logs in to dev portal.
    Used for some routes like /projects that should not be accessed programmatically.
    """
    try:
        decoded_credentials = jwt.decode(auth_data.credentials, config.SIGNING_KEY)
        logger.debug("decoded credentials", extra={"credentials": decoded_credentials})
        decoded_credentials.validate()  # This will raise a JoseError if validation fails

        user_id: str = decoded_credentials.get("sub")
        if not user_id:
            raise InvalidBearerToken("Token is missing 'sub' claim.")

        user = crud.users.get_user_by_id(db_session, UUID(user_id))
        if not user:
            logger.error(
                "user decoded from http bearer token not found", extra={"user_id": user_id}
            )
            raise UserNotFound(f"user={user_id} not found")

        logger.info("http bearer token validation successful", extra={"user_id": user_id})
        return user

    except JoseError:
        logger.exception("http bearer token validation failed")
        raise InvalidBearerToken("token validation failed")


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

    now: datetime = datetime.now(timezone.utc)
    need_reset = now >= project.daily_quota_reset_at.replace(tzinfo=timezone.utc) + timedelta(
        days=1
    )

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
    project: Annotated[Project, Depends(validate_project_quota)],
) -> RequestContext:
    """
    Returns a RequestContext object containing the DB session,
    the validated API key ID, and the project ID.
    """
    logger.info(
        "populating request context",
        extra={"api_key_id": api_key_id, "project_id": project.id},
    )
    return RequestContext(
        db_session=db_session,
        api_key_id=api_key_id,
        project=project,
    )
