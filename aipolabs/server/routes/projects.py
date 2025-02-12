from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Agent, Project, User
from aipolabs.common.enums import OrganizationRole
from aipolabs.common.exceptions import AgentNotFound, ProjectNotFound
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.agent import AgentCreate, AgentPublic, AgentUpdate
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
        body.custom_instructions,
    )
    db_session.commit()
    logger.info(f"Created agent: {AgentPublic.model_validate(agent)}")
    return agent


@router.patch("/{project_id}/agents/{agent_id}", response_model=AgentPublic, include_in_schema=True)
async def update_agent(
    project_id: UUID,
    agent_id: UUID,
    body: AgentUpdate,
    user: Annotated[User, Depends(deps.validate_http_bearer)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Agent:
    logger.info(f"Updating agent={agent_id} in project={project_id}")
    agent = crud.projects.get_agent_by_id(db_session, agent_id)
    if not agent:
        logger.error(f"agent={agent_id} not found in project={project_id}")
        raise AgentNotFound(f"agent={agent_id} not found in project={project_id}")
    # TODO: get project direct from agent through relationship
    project = crud.projects.get_project(db_session, project_id)
    if not project:
        logger.error(f"project={project_id} not found")
        raise ProjectNotFound(f"project={project_id} not found")

    if agent.project_id != project_id:
        logger.error(f"agent={agent_id} is not in project={project_id}")
        raise AgentNotFound(f"agent={agent_id} not found in project={project_id}")

    acl.validate_user_access_to_project(db_session, user.id, agent.project_id)

    crud.projects.update_agent(db_session, agent, body)
    db_session.commit()

    return agent
