from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Agent, Project, User
from aipolabs.common.enums import OrganizationRole
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.agent import AgentCreate, AgentPublic
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
