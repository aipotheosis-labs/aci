import logging
from uuid import UUID

from propelauth_fastapi import FastAPIAuth, User, init_auth
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.enums import OrganizationRole
from aci.common.exceptions import ProjectNotFound
from aci.server import config

logger = logging.getLogger(__name__)


_auth = init_auth(config.PROPELAUTH_AUTH_URL, config.PROPELAUTH_API_KEY)


def get_propelauth() -> FastAPIAuth:
    return _auth


def validate_user_access_to_org(user: User, org_id: UUID) -> None:
    # TODO: Change to require_org_member_with_minimum_role and require_org_member once projects have been refactored to use
    # TODO: org_id in the header. Currently they we have project_id so this function and validate_user_access_to_project are still useful.
    # Use PropelAuth's built-in method to validate organization role
    get_propelauth().require_org_member(user, str(org_id))


def validate_user_access_to_project(db_session: Session, user: User, project_id: UUID) -> None:
    # TODO: refactor to use PropelAuth built-in methods
    # TODO: we can introduce project level ACLs later
    project = crud.projects.get_project(db_session, project_id)
    if not project:
        raise ProjectNotFound(f"project={project_id} not found")

    validate_user_access_to_org(user, project.org_id)


def require_org_member(user: User, org_id: UUID) -> None:
    get_propelauth().require_org_member(user, str(org_id))


def require_org_member_with_minimum_role(
    user: User, org_id: UUID, minimum_role: OrganizationRole
) -> None:
    get_propelauth().require_org_member_with_minimum_role(user, str(org_id), minimum_role)
