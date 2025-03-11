from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App
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


@router.get("", response_model=list[AppDetails])
async def list_apps(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[AppsList, Query()],
) -> list[App]:
    """
    Get a list of Apps and their details. Sorted by App name.
    """
    logger.info(
        "list apps",
        extra={
            "apps_list": query_params.model_dump(exclude_none=True),
        },
    )

    return crud.apps.get_apps(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        query_params.app_names,
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
    logger.info(
        "search apps",
        extra={
            "apps_search": query_params.model_dump(exclude_none=True),
        },
    )
    intent_embedding = (
        openai_service.generate_embedding(
            query_params.intent,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )
        if query_params.intent
        else None
    )
    logger.debug(
        "generated intent embedding",
        extra={"intent": query_params.intent, "intent_embedding": intent_embedding},
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

    apps: list[AppBasic] = []
    for app, _ in apps_with_scores:
        apps.append(AppBasic.model_validate(app))

    logger.info("search apps response", extra={"app_names": [app.name for app in apps]})

    return apps


@router.get("/{app_name}", response_model=AppBasicWithFunctions)
async def get_app_details(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    app_name: str,
) -> AppBasicWithFunctions:
    """
    Returns an application (name, description, and functions).
    """
    logger.info("get app details", extra={"app_name": app_name})

    app = crud.apps.get_app(
        context.db_session,
        app_name,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )

    if not app:
        logger.error("app not found", extra={"app_name": app_name})

        raise AppNotFound(f"app={app_name} not found")

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
