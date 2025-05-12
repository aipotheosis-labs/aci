from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aci.common.db import crud
from aci.common.db.sql_models import AppConfiguration
from aci.common.enums import Visibility
from aci.common.exceptions import (
    AppConfigurationAlreadyExists,
    AppConfigurationNotFound,
    AppNotFound,
    AppSecuritySchemeNotSupported,
)
from aci.common.logging_setup import get_logger
from aci.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
    AppConfigurationsList,
    AppConfigurationUpdate,
)
from aci.server import config
from aci.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)


# TODO: when creating an app configuration, allow user to specify list of agents that are allowed to access the app
@router.post("", response_model=AppConfigurationPublic, response_model_exclude_none=True)
async def create_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    body: AppConfigurationCreate,
) -> AppConfiguration:
    """Create an app configuration for a project"""
    logger.info(
        "create app configuration",
        extra={"app_configuration_create": body.model_dump(exclude_none=True)},
    )
    # TODO: validate security scheme
    app = crud.apps.get_app(
        context.db_session,
        body.app_name,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )
    if not app:
        logger.error(
            "app not found",
            extra={"app_name": body.app_name},
        )
        raise AppNotFound(f"app={body.app_name} not found")

    if crud.app_configurations.app_configuration_exists(
        context.db_session, context.project.id, body.app_name
    ):
        logger.error(
            "app configuration already exists",
            extra={"app_name": body.app_name},
        )
        raise AppConfigurationAlreadyExists(
            f"app={body.app_name} already configured for project={context.project.id}"
        )

    if app.security_schemes.get(body.security_scheme) is None:
        logger.error(
            "app does not support specified security scheme",
            extra={
                "app_name": body.app_name,
                "security_scheme": body.security_scheme,
            },
        )
        raise AppSecuritySchemeNotSupported(
            f"app={body.app_name} does not support security_scheme={body.security_scheme}"
        )
    app_configuration = crud.app_configurations.create_app_configuration(
        context.db_session,
        context.project.id,
        body,
    )
    context.db_session.commit()

    return app_configuration


@router.get("", response_model=list[AppConfigurationPublic], response_model_exclude_none=True)
async def list_app_configurations(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[AppConfigurationsList, Query()],
) -> list[AppConfiguration]:
    """List all app configurations for a project, with optionally filters"""
    logger.info(
        "list app configurations",
        extra={"app_configurations_list": query_params.model_dump(exclude_none=True)},
    )
    return crud.app_configurations.get_app_configurations(
        context.db_session,
        context.project.id,
        query_params.app_names,
        query_params.limit,
        query_params.offset,
    )


@router.get("/{app_name}", response_model=AppConfigurationPublic, response_model_exclude_none=True)
async def get_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_name: str,
) -> AppConfiguration:
    """Get an app configuration by app name"""
    logger.info(
        "get app configuration",
        extra={"app_name": app_name},
    )
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, app_name
    )
    if not app_configuration:
        logger.error(
            "app configuration not found",
            extra={"app_name": app_name},
        )
        raise AppConfigurationNotFound(
            f"configuration for app={app_name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{app_name}"
        )
    return app_configuration


@router.delete("/{app_name}")
async def delete_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_name: str,
) -> None:
    """
    Delete an app configuration by app name
    Warning: This will delete the app configuration from the project,
    associated linked accounts, and then the app configuration record itself.
    """
    logger.info(
        "delete app configuration",
        extra={"app_name": app_name},
    )
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, app_name
    )
    if not app_configuration:
        logger.error(
            "app configuration not found",
            extra={"app_name": app_name},
        )
        raise AppConfigurationNotFound(
            f"configuration for app={app_name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{app_name}"
        )

    # TODO: double check atomic operations like below in other api endpoints
    # 1. Delete all linked accounts for this app configuration
    number_of_linked_accounts_deleted = crud.linked_accounts.delete_linked_accounts(
        context.db_session, context.project.id, app_name
    )
    logger.warning(
        "deleted linked accounts",
        extra={
            "number_of_linked_accounts_deleted": number_of_linked_accounts_deleted,
            "app_name": app_name,
        },
    )
    # 2. Delete the app configuration record
    crud.app_configurations.delete_app_configuration(
        context.db_session, context.project.id, app_name
    )

    # 3. delete this App from all agents' allowed_apps if exists
    crud.projects.delete_app_from_agents_allowed_apps(
        context.db_session, context.project.id, app_name
    )

    context.db_session.commit()


@router.patch(
    "/{app_name}", response_model=AppConfigurationPublic, response_model_exclude_none=True
)
async def update_app_configuration(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_name: str,
    body: AppConfigurationUpdate,
) -> AppConfiguration:
    """
    Update an app configuration by app name.
    If a field is not included in the request body, it will not be changed.
    """
    logger.info(
        "update app configuration",
        extra={
            "app_name": app_name,
            "app_configuration_update": body.model_dump(exclude_none=True),
        },
    )
    # validations
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, app_name
    )
    if not app_configuration:
        logger.error(
            "app configuration not found",
            extra={"app_name": app_name},
        )
        raise AppConfigurationNotFound(
            f"configuration for app={app_name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{app_name}"
        )

    crud.app_configurations.update_app_configuration(context.db_session, app_configuration, body)
    context.db_session.commit()

    return app_configuration
