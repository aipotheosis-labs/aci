from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.agent import AgentCreate, AgentPublic
from aipolabs.common.schemas.project import ProjectCreate, ProjectPublic
from aipolabs.server import dependencies as deps

# Create router instance
router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=ProjectPublic, include_in_schema=True)
async def create_project(
    body: ProjectCreate,
    user_id: Annotated[UUID, Depends(deps.validate_http_bearer)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Any:
    try:
        logger.info(f"Creating project: {body}, user_id: {user_id}")
        owner_id = body.organization_id or user_id
        # if project is to be created under an organization, check if user has admin access to the organization
        if body.organization_id:
            if not crud.user_has_admin_access_to_org(db_session, user_id, body.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have admin access to the organization",
                )

        db_project = crud.create_project(db_session, owner_id, body.name)
        db_session.commit()
        logger.info(f"Created project: {db_project}")
        return db_project
    except Exception:
        logger.error("Error in creating project", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


@router.post("/{project_id}/agents/", response_model=AgentPublic, include_in_schema=True)
async def create_agent(
    project_id: UUID,
    body: AgentCreate,
    user_id: Annotated[UUID, Depends(deps.validate_http_bearer)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> sql_models.Agent:
    try:
        logger.info(f"Creating agent in project: {project_id}, user_id: {user_id}")
        # Check if the user has admin access to the project
        if not crud.user_has_admin_access_to_project(db_session, user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have admin access to the project",
            )

        db_agent = crud.create_agent(
            db_session,
            project_id,
            body.name,
            body.description,
            body.excluded_apps,
            body.excluded_functions,
        )
        db_session.commit()
        logger.info(f"Created agent: {AgentPublic.model_validate(db_agent)}")
        return db_agent
    except Exception:
        logger.error("Error in creating agent", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent",
        )
