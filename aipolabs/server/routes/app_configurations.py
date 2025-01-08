from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import AppConfiguration
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
    AppConfigurationUpdate,
)
from aipolabs.server import dependencies as deps
from aipolabs.server.validations import validate_project_access

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=AppConfigurationPublic)
async def create_app_configuration(
    payload: AppConfigurationCreate,
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> AppConfiguration:
    """Create an app configuration for a project"""
    # TODO: validation
    # - security config is valid
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    db_app = crud.apps.get_app(db_session, payload.app_id)
    if not db_app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    if not db_app.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="App is not enabled")
    validate_project_access(db_project, db_app)
    if crud.app_configurations.app_configuration_exists(db_session, db_project.id, db_app.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App is already configured for the project",
        )
    logger.warning(f"db_app.security_schemes: {db_app.security_schemes}")
    if db_app.security_schemes.get(payload.security_scheme) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security scheme is not supported by the app",
        )
    db_app_configuration = crud.app_configurations.create_app_configuration(
        db_session,
        db_project.id,
        db_app.id,
        payload.security_scheme,
        payload.security_config_overrides,
        all_functions_enabled=True,
        enabled_functions=[],
    )
    db_session.commit()

    return db_app_configuration
    # TODO: global exception handling for none HTTPException


# TODO: add pagination
@router.get("/", response_model=list[AppConfigurationPublic])
async def list_app_configurations(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    app_id: UUID | None = None,
) -> list[AppConfiguration]:
    """List all app configurations for a project, optionally filtered by app id"""
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    return crud.app_configurations.get_app_configurations(db_session, db_project.id, app_id=app_id)


@router.get("/{app_id}", response_model=AppConfigurationPublic)
async def get_app_configuration(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    app_id: UUID,
) -> AppConfiguration:
    """Get an app configuration by app id"""
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    db_app_configuration = crud.app_configurations.get_app_configuration(
        db_session, db_project.id, app_id
    )
    if not db_app_configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="App configuration not found"
        )
    if db_app_configuration.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The app configuration does not belong to the project",
        )
    return db_app_configuration


@router.delete("/{app_id}")
async def delete_app_configuration(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    app_id: UUID,
) -> None:
    """
    Delete an app configuration by app id
    Warning: This will delete the app configuration from the project,
    associated linked accounts, and then the app configuration record itself.
    """
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    db_app_configuration = crud.app_configurations.get_app_configuration(
        db_session, db_project.id, app_id
    )
    # validations
    if not db_app_configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="App configuration not found"
        )
    if db_app_configuration.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The app configuration does not belong to the project",
        )
    # TODO: double check atomic operations like below from other api endpoints
    # 1. Delete all linked accounts for this app configuration
    crud.linked_accounts.delete_linked_accounts(db_session, db_project.id, app_id)
    # 2. Delete the app configuration record
    crud.app_configurations.delete_app_configuration(db_session, db_project.id, app_id)
    db_session.commit()


@router.patch("/{app_id}", response_model=AppConfigurationPublic)
async def update_app_configuration(
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
    app_id: UUID,
    payload: AppConfigurationUpdate,
) -> AppConfiguration:
    """
    Update an app configuration by app id.
    If a field is not included in the request body, it will not be changed.
    """
    # validations
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    db_app_configuration = crud.app_configurations.get_app_configuration(
        db_session, db_project.id, app_id
    )
    if not db_app_configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="App configuration not found"
        )
    if db_app_configuration.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The app configuration does not belong to the project",
        )

    # update only non-null fields
    if payload.security_scheme is not None:
        db_app_configuration.security_scheme = payload.security_scheme
    if payload.security_config_overrides is not None:
        db_app_configuration.security_config_overrides = payload.security_config_overrides
    if payload.enabled is not None:
        db_app_configuration.enabled = payload.enabled
    if payload.all_functions_enabled is not None:
        db_app_configuration.all_functions_enabled = payload.all_functions_enabled
    if payload.enabled_functions is not None:
        db_app_configuration.enabled_functions = payload.enabled_functions

    db_session.commit()

    return db_app_configuration
