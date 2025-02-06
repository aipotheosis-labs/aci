from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from aipolabs.common.db import crud
from aipolabs.common.enums import Visibility
from aipolabs.common.exceptions import AppNotFound
from aipolabs.common.logging import get_logger
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.app import (
    AppBasic,
    AppBasicWithFunctions,
    AppDetails,
    AppsList,
    AppsSearch,
)
from aipolabs.common.schemas.function import FunctionBasic
from aipolabs.server import config
from aipolabs.server import dependencies as deps

logger = get_logger(__name__)
router = APIRouter()
openai_service = OpenAIService(config.OPENAI_API_KEY)


@router.get("/", response_model=list[AppDetails])
async def list_apps(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[AppsList, Query()],
) -> list[AppDetails]:
    """
    Get a list of Apps and their details. Sorted by App name.
    """
    return crud.apps.get_apps(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        query_params.app_ids,
        query_params.limit,
        query_params.offset,
    )


@router.get("/search", response_model=list[AppBasic])
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
    logger.info(f"Getting apps with filter params: {query_params}")
    intent_embedding = (
        openai_service.generate_embedding(
            query_params.intent,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )
        if query_params.intent
        else None
    )
    logger.debug(f"Generated intent embedding: {intent_embedding}")

    # If configured_only is False, None is passed to the search_apps function and no filtering is done
    configured_app_ids = None
    if query_params.configured_only:
        configured_app_ids = crud.app_configurations.get_configured_app_ids(
            context.db_session,
            context.project.id,
        )
        # if no apps are configured, return an empty list
        if not configured_app_ids:
            return []

    apps_with_scores = crud.apps.search_apps(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        configured_app_ids,
        query_params.categories,
        intent_embedding,
        query_params.limit,
        query_params.offset,
    )

    # build apps list with similarity scores if they exist
    apps: list[AppBasic] = []
    for app, _ in apps_with_scores:
        app = AppBasic.model_validate(app)
        apps.append(app)

    return apps


@router.get("/{app_id}", response_model=AppBasicWithFunctions)
async def get_app_details(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_id: UUID,
) -> AppBasicWithFunctions:
    """
    Returns an application (name, description, and functions).
    """
    app = crud.apps.get_app(
        context.db_session,
        app_id,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )
    if not app:
        logger.error(f"app={app_id} not found")
        raise AppNotFound(str(app_id))

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

    app_details: AppBasicWithFunctions = AppBasicWithFunctions(
        name=app.name,
        description=app.description,
        functions=[FunctionBasic.model_validate(function) for function in functions],
    )

    return app_details
