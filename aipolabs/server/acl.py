import logging
from uuid import UUID

from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Function, Project
from aipolabs.common.enums import OrganizationRole, Visibility
from aipolabs.common.exceptions import (
    AppAccessDenied,
    FunctionAccessDenied,
    ProjectAccessDenied,
    ProjectNotFound,
)

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
        logger.error(f"project not found, project={project_id}")
        raise ProjectNotFound(str(project_id))
    if project.owner_id != user_id:
        logger.error(f"user={user_id} does not have access to project={project_id}")
        raise ProjectAccessDenied(f"access denied to project={project_id}")


def validate_project_access_to_app(project: Project, app: App) -> None:
    if project.visibility_access == Visibility.PUBLIC and app.visibility != Visibility.PUBLIC:
        logger.error(f"project={project.id} does not have access to app={app.id}")
        raise AppAccessDenied(f"access denied to app={app.id}")


def validate_project_access_to_function(project: Project, function: Function) -> None:
    if project.visibility_access == Visibility.PUBLIC and (
        function.visibility != Visibility.PUBLIC or function.app.visibility != Visibility.PUBLIC
    ):
        logger.error(f"project={project.id} does not have access to function={function.id}")
        raise FunctionAccessDenied(f"access denied to function={function.id}")
