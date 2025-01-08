from uuid import UUID

from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.enums import OrganizationRole


# TODO: centralize exceptions and exception handling
class ProjectNotFoundError(Exception):
    """Exception raised when a project is not found in the database."""

    pass


# TODO: implement this
def validate_user_access_to_org(
    db_session: Session, user_id: UUID, org_id: UUID, org_type: OrganizationRole
) -> bool:
    return True


def validate_user_access_to_project(db_session: Session, user_id: UUID, project_id: UUID) -> bool:
    # TODO: implement properly with organization and project access control.
    # for now, just check if project owner is the user

    project = crud.projects.get_project(db_session, project_id)
    if project:
        return bool(project.owner_id == user_id)
    else:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found")
