from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.integrations import IntegrationPublic
from aipolabs.server import dependencies as deps
from aipolabs.server.validations import validate_project_access

router = APIRouter()
logger = get_logger(__name__)


class AddIntegrationPayload(BaseModel):
    app_name: str
    security_scheme: SecurityScheme
    # TODO: add typing/class to security_config_overrides
    security_config_overrides: dict[str, Any] = Field(default_factory=dict)
    # TODO: add all_functions_enabled/enabled_functions fields


@router.post("/")
async def add_integration(
    payload: AddIntegrationPayload,
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> dict[str, UUID]:
    """Integrate an app to a project"""
    # TODO: validation
    # - security config is valid
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    db_app = crud.get_app_by_name(db_session, payload.app_name)
    if not db_app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    if not db_app.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="App is not enabled")
    validate_project_access(db_project, db_app)
    if crud.integration_exists(db_session, db_project.id, db_app.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App is already integrated to the project",
        )
    logger.warning(f"db_app.security_schemes: {db_app.security_schemes}")
    if db_app.security_schemes.get(payload.security_scheme) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security scheme is not supported by the app",
        )
    db_project_app_integration = crud.add_integration(
        db_session,
        db_project.id,
        db_app.id,
        payload.security_scheme,
        payload.security_config_overrides,
        all_functions_enabled=True,
        enabled_functions=[],
    )
    db_session.commit()

    return {"integration_id": db_project_app_integration.id}
    # TODO: global exception handling for none HTTPException


@router.get("/", response_model=list[IntegrationPublic])
async def list_integrations(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    app_name: str | None = None,
) -> list[sql_models.ProjectAppIntegration]:
    """List all integrations for a project, optionally filtered by app name"""
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    return crud.get_integrations(db_session, db_project.id, app_name=app_name)


@router.get("/{integration_id}", response_model=IntegrationPublic)
async def get_integration(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    integration_id: UUID,
) -> sql_models.ProjectAppIntegration:
    """Get an integration by id"""
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    db_integration = crud.get_integration(db_session, integration_id)
    if not db_integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    if db_integration.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The integration does not belong to the project",
        )
    return db_integration


@router.delete("/{integration_id}")
async def delete_integration(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    integration_id: UUID,
) -> None:
    """
    Delete an integration by id
    Warning: This will delete the app integration from the project,
    associated linked accounts, and then the integration record itself.
    """
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    db_integration = crud.get_integration(db_session, integration_id)
    # validations
    if not db_integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    if db_integration.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The integration does not belong to the project",
        )
    # TODO: double check atomic operations like below from other api endpoints
    # 1. Delete all linked accounts for this integration
    crud.delete_accounts(db_session, integration_id)
    # 2. Delete the integration record
    crud.delete_integration(db_session, integration_id)
    db_session.commit()
