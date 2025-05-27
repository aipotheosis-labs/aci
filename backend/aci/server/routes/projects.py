from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from propelauth_fastapi import User
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Project
from aci.common.enums import OrganizationRole
from aci.common.logging_setup import get_logger
from aci.common.schemas.project import ProjectCreate, ProjectPublic
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
