from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import AppConfiguration
from aipolabs.common.enums import Visibility
from aipolabs.common.exceptions import (
    AppConfigurationAlreadyExists,
    AppConfigurationNotFound,
    AppNotFound,
    AppSecuritySchemeNotSupported,
    UnexpectedException,
)
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
    AppConfigurationsList,
    AppConfigurationUpdate,
)
from aipolabs.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=AppConfigurationPublic)
async def create_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    body: AppConfigurationCreate,
) -> AppConfiguration:
    """Create an app configuration for a project"""
    # TODO: validate security scheme
    app = crud.apps.get_app(
        context.db_session,
        body.app_id,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )
    if not app:
        logger.error(f"app={body.app_id} not found")
        raise AppNotFound(str(body.app_id))

    if crud.app_configurations.app_configuration_exists(
        context.db_session, context.project.id, body.app_id
    ):
        logger.error(
            f"app configuration already exists for app={body.app_id}, project={context.project.id}"
        )
        raise AppConfigurationAlreadyExists(
            f"app={body.app_id} already configured for project={context.project.id}"
        )

    if app.security_schemes.get(body.security_scheme) is None:
        logger.error(f"app={body.app_id} does not support security_scheme={body.security_scheme}")
        raise AppSecuritySchemeNotSupported(
            f"app={body.app_id} does not support security_scheme={body.security_scheme}"
        )
    app_configuration = crud.app_configurations.create_app_configuration(
        context.db_session,
        context.project.id,
        body,
    )
    context.db_session.commit()

    return app_configuration


@router.get("/", response_model=list[AppConfigurationPublic])
async def list_app_configurations(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[AppConfigurationsList, Query()],
) -> list[AppConfiguration]:
    """List all app configurations for a project, with optionally filters"""
    return crud.app_configurations.get_app_configurations(
        context.db_session,
        context.project.id,
        query_params.app_id,
        query_params.limit,
        query_params.offset,
    )


@router.get("/{app_id}", response_model=AppConfigurationPublic)
async def get_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_id: UUID,
) -> AppConfiguration:
    """Get an app configuration by app id"""
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, app_id
    )
    if not app_configuration:
        logger.error(f"app configuration not found for app={app_id}, project={context.project.id}")
        raise AppConfigurationNotFound(
            f"configuration for app={app_id} not found for project={context.project.id}"
        )
    return app_configuration


@router.delete("/{app_id}")
async def delete_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_id: UUID,
) -> None:
    """
    Delete an app configuration by app id
    Warning: This will delete the app configuration from the project,
    associated linked accounts, and then the app configuration record itself.
    """
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, app_id
    )
    if not app_configuration:
        logger.error(f"app configuration not found, app={app_id}, project={context.project.id}")
        raise AppConfigurationNotFound(
            f"configuration for app={app_id} not found for project={context.project.id}"
        )

    # TODO: double check atomic operations like below in other api endpoints
    # 1. Delete all linked accounts for this app configuration
    crud.linked_accounts.delete_linked_accounts(context.db_session, context.project.id, app_id)
    # 2. Delete the app configuration record
    deleted_count = crud.app_configurations.delete_app_configuration(
        context.db_session, context.project.id, app_id
    )
    if deleted_count != 1:
        logger.error(
            f"unexpected error deleting app configuration for app={app_id}, project={context.project.id}, "
            f"wrong number of rows will be deleted={deleted_count}"
        )
        raise UnexpectedException(
            f"unexpected error deleting app configuration for app={app_id}, project={context.project.id}, "
            f"wrong number of rows will be deleted={deleted_count}"
        )
    context.db_session.commit()


@router.patch("/{app_id}", response_model=AppConfigurationPublic)
async def update_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_id: UUID,
    body: AppConfigurationUpdate,
) -> AppConfiguration:
    """
    Update an app configuration by app id.
    If a field is not included in the request body, it will not be changed.
    """
    # validations
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, app_id
    )
    if not app_configuration:
        logger.error(f"app configuration not found, app={app_id}, project={context.project.id}")
        raise AppConfigurationNotFound(
            f"configuration for app={app_id} not found for project={context.project.id}"
        )

    crud.app_configurations.update_app_configuration(context.db_session, app_configuration, body)
    context.db_session.commit()

    return app_configuration
