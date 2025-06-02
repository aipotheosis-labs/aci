from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from propelauth_fastapi import User
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Project
from aci.common.enums import OrganizationRole
from aci.common.exceptions import (
    ProjectIsLastInOrgError,
    ProjectNotFound,
)
from aci.common.logging_setup import get_logger
from aci.common.schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate
from aci.server import acl, quota_manager
from aci.server import dependencies as deps

# Create router instance
router = APIRouter()
logger = get_logger(__name__)

auth = acl.get_propelauth()


@router.post("", response_model=ProjectPublic, include_in_schema=True)
async def create_project(
    body: ProjectCreate,
    user: Annotated[User, Depends(auth.require_user)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Project:
    logger.info(
        "create project",
        extra={
            "project_create": body.model_dump(exclude_none=True),
            "user_id": user.user_id,
            "org_id": body.org_id,
        },
    )

    acl.validate_user_access_to_org(user, body.org_id, OrganizationRole.OWNER)
    quota_manager.enforce_project_creation_quota(db_session, body.org_id)

    project = crud.projects.create_project(db_session, body.org_id, body.name)

    # Create a default Agent for the project
    crud.agents.create_agent(
        db_session,
        project.id,
        name="Default Agent",
        description="Default Agent",
        allowed_apps=[],
        custom_instructions={},
    )
    db_session.commit()

    logger.info(
        "created project",
        extra={"project_id": project.id, "user_id": user.user_id, "org_id": body.org_id},
    )
    return project


@router.get("", response_model=list[ProjectPublic], include_in_schema=True)
async def get_projects(
    user: Annotated[User, Depends(auth.require_user)],
    org_id: Annotated[UUID, Header(alias="X-ACI-ORG-ID")],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> list[Project]:
    """
    Get all projects that the user is the owner of
    """
    acl.validate_user_access_to_org(user, org_id, OrganizationRole.OWNER)

    logger.info(
        "get projects",
        extra={
            "user_id": user.user_id,
            "org_id": org_id,
        },
    )

    projects = crud.projects.get_projects_by_org(db_session, org_id)

    return projects


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=True)
async def delete_project(
    project_id: UUID,
    user: Annotated[User, Depends(auth.require_user)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> None:
    """
    Delete a project by project id.

    This operation will cascade delete all related data:
    - Agents and their API keys
    - App configurations
    - Linked accounts

    All associations to the project will be removed from the database.
    """
    logger.info(
        "delete project",
        extra={"project_id": project_id, "user_id": user.user_id},
    )

    acl.validate_user_access_to_project(db_session, user, project_id)

    # Get the project to check its organization
    project = crud.projects.get_project(db_session, project_id)
    if not project:
        logger.error(
            "project not found",
            extra={"project_id": project_id},
        )
        raise ProjectNotFound(f"project={project_id} not found")

    # Check if this is the last project in the organization
    org_projects = crud.projects.get_projects_by_org(db_session, project.org_id)
    if len(org_projects) <= 1:
        logger.error(
            "cannot delete last project",
            extra={"project_id": project_id, "org_id": project.org_id},
        )
        raise ProjectIsLastInOrgError()

    crud.projects.delete_project(db_session, project_id)
    db_session.commit()


@router.patch("/{project_id}", response_model=ProjectPublic, include_in_schema=True)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    user: Annotated[User, Depends(auth.require_user)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Project:
    """
    Update a project by project id.
    Currently supports updating the project name.
    """
    logger.info(
        "update project",
        extra={
            "project_id": project_id,
            "project_update": body.model_dump(exclude_none=True),
            "user_id": user.user_id,
        },
    )

    acl.validate_user_access_to_project(db_session, user, project_id)

    project = crud.projects.get_project(db_session, project_id)
    if not project:
        logger.error(
            "project not found",
            extra={"project_id": project_id},
        )
        raise ProjectNotFound(f"project={project_id} not found")

    updated_project = crud.projects.update_project(db_session, project, body)
    db_session.commit()

    return updated_project
