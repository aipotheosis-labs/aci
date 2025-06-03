import logging
from uuid import UUID

from propelauth_fastapi import FastAPIAuth, User, init_auth
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.enums import OrganizationRole
from aci.common.exceptions import OrgAccessDenied, ProjectNotFound
from aci.server import config

logger = logging.getLogger(__name__)


_auth = init_auth(config.PROPELAUTH_AUTH_URL, config.PROPELAUTH_API_KEY)


def get_propelauth() -> FastAPIAuth:
    return _auth


def validate_user_access_to_org(user: User, org_id: UUID, org_role: OrganizationRole) -> None:
    # TODO: refactor to use PropelAuth built-in methods
    org = user.get_org(str(org_id))
    # TODO: may need to check user_inherited_roles_plus_current_role for project level ACLs
    if (org is None) or (org.user_is_role(org_role) is False):
        raise OrgAccessDenied(
            f"user={user.user_id} does not have access to org={org_id} or "
            f"does not have the required role={org_role} in the org"
        )


def validate_user_access_to_project(db_session: Session, user: User, project_id: UUID) -> None:
    # TODO: refactor to use PropelAuth built-in methods
    # TODO: we can introduce project level ACLs later
    project = crud.projects.get_project(db_session, project_id)
    if not project:
        raise ProjectNotFound(f"project={project_id} not found")

    validate_user_access_to_org(user, project.org_id, OrganizationRole.OWNER)


def require_org_member(user: User, org_id: UUID) -> None:
    get_propelauth().require_org_member(user, str(org_id))


def require_org_member_with_minimum_role(
    user: User, org_id: UUID, minimum_role: OrganizationRole
) -> None:
    get_propelauth().require_org_member_with_minimum_role(user, str(org_id), minimum_role)
