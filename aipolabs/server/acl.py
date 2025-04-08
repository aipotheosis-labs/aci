import logging
from uuid import UUID

from fastapi import HTTPException
from propelauth_fastapi import FastAPIAuth, User, init_auth
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.exceptions import ProjectNotFound
from aipolabs.server import config

logger = logging.getLogger(__name__)


_auth = init_auth(config.PROPELAUTH_AUTH_URL, config.PROPELAUTH_API_KEY)


def setup_propelauth() -> FastAPIAuth:
    return _auth


def validate_user_access_to_org(user: User, org_id: UUID, org_role: str) -> None:
    org = user.get_org(str(org_id))
    if (org is None) or (org.user_is_role(org_role) is False):
        raise HTTPException(status_code=403, detail="Forbidden")


def validate_user_access_to_project(db_session: Session, user: User, project_id: UUID) -> None:
    # TODO: we can introduce project level ACLs later
    project = crud.projects.get_project(db_session, project_id)
    if not project:
        raise ProjectNotFound(f"project={project_id} not found")

    validate_user_access_to_org(user, project.org_id, "Owner")
