from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.enums import Visibility
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
from aipolabs.server.dependencies import validate_api_key, yield_db_session

logger = get_logger(__name__)
router = APIRouter()
openai_service = OpenAIService(config.OPENAI_API_KEY)


@router.get("/", response_model=list[AppDetails])
async def list_apps(
    query_params: Annotated[AppsList, Query()],
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> list[AppDetails]:
    """
    Get a list of Apps and their details. Sorted by App name.
    """
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)

    return crud.apps.get_apps(
        db_session,
        db_project.visibility_access == Visibility.PUBLIC,
        query_params.limit,
        query_params.offset,
    )


@router.get("/search", response_model=list[AppBasic])
async def search_apps(
    query_params: Annotated[AppsSearch, Query()],
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> list[AppBasic]:
    """
    Search for Apps.
    Intented to be used by agents to search for apps based on natural language intent.
    """
    # TODO: currently the search is done across all apps, we might want to add flags to account for below scenarios:
    # - when clients search for apps, if the app is not configured, should it be discoverable?
    # - when clients search for apps, if an app is configured but disabled by client, should it be discoverable?
    try:
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
        apps_with_scores = crud.apps.search_apps(
            db_session,
            api_key_id,
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
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error getting apps with filter params: {query_params}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{app_id}", response_model=AppBasicWithFunctions)
async def get_app_details(
    app_id: UUID,
    db_session: Annotated[Session, Depends(yield_db_session)],
    api_key_id: Annotated[UUID, Depends(validate_api_key)],
) -> AppBasicWithFunctions:
    """
    Returns an application (name, description, and functions).
    """
    try:
        db_app = crud.apps.get_app(db_session, app_id)
        if not db_app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found.")

        if not db_app.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="App is currently disabled."
            )

        db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
        # TODO: unify access control logic
        if (
            db_project.visibility_access == Visibility.PUBLIC
            and db_app.visibility != Visibility.PUBLIC
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this app.",
            )
        # filter functions by project visibility and enabled status
        # TODO: better way and place for this logic?
        db_functions = [
            function
            for function in db_app.functions
            if function.enabled
            and not (
                db_project.visibility_access == Visibility.PUBLIC
                and function.visibility != Visibility.PUBLIC
            )
        ]

        app_details: AppBasicWithFunctions = AppBasicWithFunctions(
            name=db_app.name,
            description=db_app.description,
            functions=[FunctionBasic.model_validate(function) for function in db_functions],
        )

        return app_details
    except HTTPException as e:
        raise e
    # TODO: is catching Exception here necessary?
    except Exception as e:
        logger.exception(f"Error getting app: {app_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
