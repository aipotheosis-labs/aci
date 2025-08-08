from typing import Annotated

from aci.common.db.crud.app_configurations import get_app_configuration
from fastapi import APIRouter, Depends, Query
from openai import OpenAI

from aci.common.db import crud
from aci.common.embeddings import generate_embedding
from aci.common.enums import Visibility
from aci.common.exceptions import AppNotFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.app import (
    AppBasic,
    AppDetails,
    AppsList,
    AppsSearch,
)
from aci.common.schemas.function import BasicFunctionDefinition, BasicFunctionDefinitionWithEnabled, FunctionDetails, FunctionDetailsWithEnabled
from aci.common.schemas.security_scheme import SecuritySchemesPublic
from aci.server import config
from aci.server import dependencies as deps

logger = get_logger(__name__)
router = APIRouter()
# TODO: will this be a bottleneck and problem if high concurrent requests from users?
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)


@router.get("", response_model_exclude_none=True)
async def list_apps(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[AppsList, Query()],
) -> list[AppDetails]:
    """
    Get a list of Apps and their details. Sorted by App name.
    """
    apps = crud.apps.get_apps(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        query_params.app_names,
        query_params.limit,
        query_params.offset,
    )

    # Find what functions are enabled for each app with single query
    app_configs = crud.app_configurations.get_app_configurations(
        context.db_session,
        context.project.id,
        query_params.app_names,
        None,
        None,
    )
    enabled_function_names: list[str] = []
    for app_config in app_configs:
        if app_config.enabled:
            if app_config.all_functions_enabled:
                enabled_function_names.extend([function.name for function in app_config.app.functions])
            else:
                enabled_function_names.extend(app_config.enabled_functions)

    response: list[AppDetails] = []
    for app in apps:

        functions: list[FunctionDetailsWithEnabled] = []
        for app_function in app.functions:
            functions.append(FunctionDetailsWithEnabled.model_validate({
                **FunctionDetails.model_validate(app_function).model_dump(),
                "enabled": app_function.name in enabled_function_names,
            }))

        app_details = AppDetails(
            id=app.id,
            name=app.name,
            display_name=app.display_name,
            provider=app.provider,
            version=app.version,
            description=app.description,
            logo=app.logo,
            categories=app.categories,
            visibility=app.visibility,
            active=app.active,
            security_schemes=list(app.security_schemes.keys()),
            # TODO: check validation latency
            supported_security_schemes=SecuritySchemesPublic.model_validate(app.security_schemes),
            functions=functions,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )
        response.append(app_details)

    return response


@router.get("/search", response_model_exclude_none=True)
async def search_apps(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[AppsSearch, Query()],
) -> list[AppBasic]:
    """
    Search for Apps.
    Intented to be used by agents to search for apps based on natural language intent.
    """
    # TODO: currently the search is done across all apps, we might want to add flags to account for below scenarios:
    # - when clients search for apps, if an app is configured but disabled by client, should it be discoverable?
    intent_embedding = (
        generate_embedding(
            openai_client,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
            query_params.intent,
        )
        if query_params.intent
        else None
    )
    logger.debug(
        f"Generated intent embedding, intent={query_params.intent}, intent_embedding={intent_embedding}"
    )
    # if the search is restricted to allowed apps, we need to filter the apps by the agent's allowed apps.
    # None means no filtering
    apps_to_filter = context.agent.allowed_apps if query_params.allowed_apps_only else None

    apps_with_scores = crud.apps.search_apps(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        apps_to_filter,
        query_params.categories,
        intent_embedding,
        query_params.limit,
        query_params.offset,
    )

    # Find what functions are enabled for each app with single query
    app_configs = crud.app_configurations.get_app_configurations(
        context.db_session,
        context.project.id,
        apps_to_filter,
        None,
        None,
    )
    enabled_function_names: list[str] = []
    for app_config in app_configs:
        if app_config.enabled:
            if app_config.all_functions_enabled:
                enabled_function_names.extend([function.name for function in app_config.app.functions])
            else:
                enabled_function_names.extend(app_config.enabled_functions)


    apps: list[AppBasic] = []

    for app, _ in apps_with_scores:
        if query_params.include_functions:
            functions = [
                BasicFunctionDefinitionWithEnabled(name=function.name, description=function.description, enabled=function.name in enabled_function_names)
                for function in app.functions
            ]
            apps.append(AppBasic(name=app.name, description=app.description, functions=functions))
        else:
            apps.append(AppBasic(name=app.name, description=app.description))

    logger.info(
        "Search apps result",
        extra={
            "search_apps": {
                "query_params_json": query_params.model_dump_json(),
                "app_names": [app.name for app, _ in apps_with_scores],
            },
        },
    )

    return apps


@router.get("/{app_name}", response_model_exclude_none=True)
async def get_app_details(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_name: str,
) -> AppDetails:
    """
    Returns an application (name, description, and functions).
    """
    app = crud.apps.get_app(
        context.db_session,
        app_name,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )

    if not app:
        logger.error(f"App not found, app_name={app_name}")

        raise AppNotFound(f"App={app_name} not found")

    # filter functions by project visibility and active status
    # TODO: better way and place for crud filtering/acl logic like this?
    functions = [
        function
        for function in app.functions
        if function.active
        and not (
            context.project.visibility_access == Visibility.PUBLIC
            and function.visibility != Visibility.PUBLIC
        )
    ]

    app_config = crud.app_configurations.get_app_configuration(
        context.db_session,
        context.project.id,
        app_name,
    )

    if app_config is None:
        enabled_function_names = []
    else:
        if app_config.all_functions_enabled:
            enabled_function_names = [function.name for function in app.functions]
        else:
            enabled_function_names = app_config.enabled_functions

    app_details: AppDetails = AppDetails(
        id=app.id,
        name=app.name,
        display_name=app.display_name,
        provider=app.provider,
        version=app.version,
        description=app.description,
        logo=app.logo,
        categories=app.categories,
        visibility=app.visibility,
        active=app.active,
        security_schemes=list(app.security_schemes.keys()),
        supported_security_schemes=SecuritySchemesPublic.model_validate(app.security_schemes),
        functions=[FunctionDetailsWithEnabled.model_validate({
            **FunctionDetails.model_validate(function).model_dump(),
            "enabled": function.name in enabled_function_names,
        }) for function in functions],
        created_at=app.created_at,
        updated_at=app.updated_at,
    )

    return app_details
