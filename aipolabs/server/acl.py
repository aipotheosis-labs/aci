import logging
from uuid import UUID

from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.enums import OrganizationRole
from aipolabs.common.exceptions import ProjectAccessDenied, ProjectNotFound

logger = logging.getLogger(__name__)


# TODO: implement this
def validate_user_access_to_org(
    db_session: Session, user_id: UUID, org_id: UUID, org_type: OrganizationRole
) -> None:
    pass


def validate_user_access_to_project(db_session: Session, user_id: UUID, project_id: UUID) -> None:
    """
    Validate user access to a project.
    """
    # TODO: implement properly with organization and project access control.
    # for now, just check if project owner is the user
    project = crud.projects.get_project(db_session, project_id)
    if not project:
        logger.error("project not found", extra={"project_id": project_id, "user_id": user_id})
        raise ProjectNotFound(f"project={project_id} not found")
    if project.owner_id != user_id:
        logger.error(
            "user does not have access to project",
            extra={"user_id": user_id, "project_id": project_id},
        )
        raise ProjectAccessDenied(f"user={user_id} does not have access to project={project_id}")
