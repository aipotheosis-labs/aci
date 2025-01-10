from datetime import datetime, timedelta, timezone
from typing import Annotated, Generator
from uuid import UUID

from authlib.jose import JoseError, jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Project
from aipolabs.common.enums import APIKeyStatus
from aipolabs.common.exceptions import ProjectNotFound
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
    auth_data: Annotated[HTTPAuthorizationCredentials, Security(http_bearer)],
) -> UUID:
    """
    Validate HTTP Bearer token and return user ID.
    HTTP Bearer token is generated after a user logs in to dev portal.
    Used for some routes like /projects that should not be accessed programmatically.
    """
    token = auth_data.credentials
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY)
        logger.debug(f"Decoded token payload: {payload}")
        payload.validate()  # This will raise a JoseError if validation fails

        user_id: str = payload.get("sub")
        if not user_id:
            logger.error("Token is missing 'sub' claim.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials, missing 'sub' claim",
            )

        logger.debug(f"Token valid. User ID: {user_id}")
        return UUID(user_id)

    except JoseError as e:
        logger.error("Token verification failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}"
        )


def validate_api_key(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key: Annotated[str, Security(api_key_header)],
) -> UUID:
    """Validate API key and return the API key ID. (not the actual API key string)"""
    db_api_key = crud.projects.get_api_key(db_session, api_key)
    if db_api_key is None:
        logger.error(f"api key not found: {api_key[:8]}****")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    if db_api_key.status == APIKeyStatus.DISABLED:
        logger.error(f"api key is disabled: {api_key[:8]}****")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is disabled")
    elif db_api_key.status == APIKeyStatus.DELETED:
        logger.error(f"api key is deleted: {api_key[:8]}****")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is deleted")

    api_key_id: UUID = db_api_key.id
    return api_key_id


# TODO: use cache (redis)
# TODO: better way to handle replace(tzinfo=datetime.timezone.utc) ?
def validate_project_quota(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> Project:
    logger.debug(f"Validating project quota for API key ID: {api_key_id}")

    project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    if not project:
        raise ProjectNotFound()

    now: datetime = datetime.now(timezone.utc)
    need_reset = now >= project.daily_quota_reset_at.replace(tzinfo=timezone.utc) + timedelta(
        days=1
    )

    if not need_reset and project.daily_quota_used >= config.PROJECT_DAILY_QUOTA:
        logger.warning(f"Daily quota exceeded for project {project.id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Daily quota exceeded")

    try:
        crud.projects.increase_project_quota_usage(db_session, project)
        # TODO: commit here?
        db_session.commit()
        return project
    except Exception as e:
        logger.exception(f"Failed to increase project quota usage for project {project.id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def get_request_context(
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
    project: Annotated[Project, Depends(validate_project_quota)],
) -> RequestContext:
    """
    Returns a RequestContext object containing the DB session,
    the validated API key ID, and the project ID.
    """
    return RequestContext(
        db_session=db_session,
        api_key_id=api_key_id,
        project=project,
    )
