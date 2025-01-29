from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Agent, Project, User
from aipolabs.common.enums import OrganizationRole, Visibility
from aipolabs.common.exceptions import AgentNotFound, AppNotFound, ProjectNotFound
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.agent import (
    AgentCreate,
    AgentPublic,
    CustomInstructionsCreate,
)
from aipolabs.common.schemas.project import ProjectCreate, ProjectPublic
from aipolabs.server import acl
from aipolabs.server import dependencies as deps

# Create router instance
router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=ProjectPublic, include_in_schema=True)
async def create_project(
    body: ProjectCreate,
    user: Annotated[User, Depends(deps.validate_http_bearer)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Project:
    logger.info(f"Creating project={body}, user={user.id}")
    owner_id = body.organization_id or user.id
    # if project is to be created under an organization, check if user has admin access to the organization
    # TODO: add tests for this path
    if body.organization_id:
        acl.validate_user_access_to_org(
            db_session, user.id, body.organization_id, OrganizationRole.ADMIN
        )

    project = crud.projects.create_project(db_session, owner_id, body.name)
    db_session.commit()
    logger.info(f"Created project: {project}")
    return project


@router.get("/", response_model=list[ProjectPublic], include_in_schema=True)
async def get_projects(
    user: Annotated[User, Depends(deps.validate_http_bearer)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> list[Project]:
    """
    Get all projects that the user is the owner of
    """
    # TODO: for now, we only support getting projects that the user is the owner of,
    # we will need to support getting projects that the user has access to (a member of an organization)
    logger.info(f"Getting projects for user={user.id}")
    projects = crud.projects.get_projects_by_owner(db_session, user.id)
    return projects


@router.post("/{project_id}/agents/", response_model=AgentPublic, include_in_schema=True)
async def create_agent(
    project_id: UUID,
    body: AgentCreate,
    user: Annotated[User, Depends(deps.validate_http_bearer)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Agent:
    logger.info(f"Creating agent in project={project_id}, user={user.id}")
    acl.validate_user_access_to_project(db_session, user.id, project_id)

    agent = crud.projects.create_agent(
        db_session,
        project_id,
        body.name,
        body.description,
        body.excluded_apps,
        body.excluded_functions,
    )
    db_session.commit()
    logger.info(f"Created agent: {AgentPublic.model_validate(agent)}")
    return agent


@router.post("/agents/{agent_id}/custom-instructions/", response_model=AgentPublic)
async def create_custom_instructions(
    agent_id: UUID,
    body: CustomInstructionsCreate,
    user: Annotated[User, Depends(deps.validate_http_bearer)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Agent:
    logger.info(f"Creating custom instructions for agent={agent_id}, and app={body.app_id}")
    # Get project id from agent
    agent = crud.projects.get_agent_by_id(db_session, agent_id)
    if not agent:
        logger.error(f"Agent not found: {agent_id}")
        raise AgentNotFound(str(agent_id))
    acl.validate_user_access_to_project(db_session, user.id, agent.project_id)

    # get project
    project = crud.projects.get_project(db_session, agent.project_id)
    if not project:
        logger.error(f"Project not found: {agent.project_id}")
        raise ProjectNotFound(str(agent.project_id))
    # Validate that the app exists
    app = crud.apps.get_app(
        db_session, body.app_id, project.visibility_access == Visibility.PUBLIC, True
    )
    if not app:
        logger.error(f"App not found: {body.app_id}")
        raise AppNotFound(str(body.app_id))

    # Update the custom_instructions dictionary
    agent.custom_instructions[str(body.app_id)] = body.instructions
    db_session.commit()
    logger.info(f"Created custom instructions for agent={agent_id}, and app={body.app_id}")
    return agent
