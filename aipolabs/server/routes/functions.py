import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from aipolabs.common import processor
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Function
from aipolabs.common.enums import Visibility
from aipolabs.common.exceptions import (
    AppConfigurationDisabled,
    AppConfigurationNotFound,
    FunctionNotFound,
    LinkedAccountDisabled,
    LinkedAccountNotFound,
)
from aipolabs.common.logging import get_logger
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.function import (
    AnthropicFunctionDefinition,
    FunctionBasic,
    FunctionDetails,
    FunctionExecute,
    FunctionExecutionResult,
    FunctionsList,
    FunctionsSearch,
    InferenceProvider,
    OpenAIFunctionDefinition,
)
from aipolabs.server import config
from aipolabs.server import dependencies as deps
from aipolabs.server.function_executors import get_executor

router = APIRouter()
logger = get_logger(__name__)
openai_service = OpenAIService(config.OPENAI_API_KEY)


@router.get("/", response_model=list[FunctionDetails])
async def list_functions(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[FunctionsList, Query()],
) -> list[Function]:
    """Get a list of functions and their details. Sorted by function name."""
    return crud.functions.get_functions(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        query_params.app_ids,
        query_params.limit,
        query_params.offset,
    )


@router.get("/search", response_model=list[FunctionBasic])
async def search_functions(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[FunctionsSearch, Query()],
) -> list[Function]:
    """
    Returns the basic information of a list of functions.
    """
    # TODO: currently the search is done across all apps, we might want to add flags to account for below scenarios:
    # - when clients search for functions, if the app of the functions is configured but disabled by client, should the functions be discoverable?
    logger.debug(f"Getting functions with params: {query_params}")
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

    if query_params.configured_only:
        configured_app_ids = crud.app_configurations.get_configured_app_ids(
            context.db_session,
            context.project.id,
        )
        # Filter app_ids based on configuration status
        if query_params.app_ids:
            # Intersection of query_params.app_ids and configured_app_ids
            query_params.app_ids = [
                app_id for app_id in query_params.app_ids if app_id in configured_app_ids
            ]
        else:
            query_params.app_ids = configured_app_ids

        # If no app_ids are available after intersection or configured search, return an empty list
        if not query_params.app_ids:
            return []

    functions = crud.functions.search_functions(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        query_params.app_ids,
        intent_embedding,
        query_params.limit,
        query_params.offset,
    )
    logger.debug(f"functions: \n {functions}")
    return functions


# TODO: have "structured_outputs" flag ("structured_outputs_if_possible") to support openai's structured outputs function calling?
# which need "strict: true" and only support a subset of json schema and a bunch of other restrictions like "All fields must be required"
# If you turn on Structured Outputs by supplying strict: true and call the API with an unsupported JSON Schema, you will receive an error.
# TODO: client sdk can use pydantic to validate model output for parameters used for function execution
# TODO: "flatten" flag to make sure nested parameters are flattened?
@router.get(
    "/{function_id}/definition",
    response_model=OpenAIFunctionDefinition | AnthropicFunctionDefinition,
    response_model_exclude_none=True,  # having this to exclude "strict" field in openai's function definition if not set
)
async def get_function_definition(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    function_id: UUID,
    inference_provider: InferenceProvider = Query(
        default=InferenceProvider.OPENAI,
        description="The inference provider, which determines the format of the function definition.",
    ),
) -> Function:
    """
    Return the function definition that can be used directly by LLM.
    The actual content depends on the intended model (inference provider, e.g., OpenAI, Anthropic, etc.) and the function itself.
    """
    function: Function | None = crud.functions.get_function(
        context.db_session,
        function_id,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )
    if not function:
        logger.error(f"function={function_id} not found")
        raise FunctionNotFound(str(function_id))

    visible_parameters = processor.filter_visible_properties(function.parameters)
    logger.debug(f"Filtered parameters: {json.dumps(visible_parameters)}")

    if inference_provider == InferenceProvider.OPENAI:
        function_definition = OpenAIFunctionDefinition(
            function={
                "name": function.name,
                "description": function.description,
                "parameters": visible_parameters,
            }
        )
    elif inference_provider == InferenceProvider.ANTHROPIC:
        function_definition = AnthropicFunctionDefinition(
            name=function.name,
            description=function.description,
            input_schema=visible_parameters,
        )
    return function_definition


# TODO: is there any way to abstract and generalize the checks and validations
# (enabled, configured, accessible, etc.)?
@router.post(
    "/{function_id}/execute",
    response_model=FunctionExecutionResult,
    response_model_exclude_none=True,
)
async def execute(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    function_id: UUID,
    body: FunctionExecute,
) -> FunctionExecutionResult:
    # Fetch function definition
    function = crud.functions.get_function(
        context.db_session,
        function_id,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )
    if not function:
        logger.error(f"function={function_id} not found")
        raise FunctionNotFound(str(function_id))

    # check if the App (that this function belongs to) is configured
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, function.app_id
    )
    if not app_configuration:
        logger.error(
            f"app configuration not found for app={function.app_id}, project={context.project.id}"
        )
        raise AppConfigurationNotFound(
            f"configuration for app={function.app_id} not found for project={context.project.id}"
        )

    # check if user has disabled the app configuration
    if not app_configuration.enabled:
        logger.error(
            f"app configuration is disabled for app={function.app_id}, project={context.project.id}"
        )
        raise AppConfigurationDisabled(
            f"configuration for app={function.app_id} is disabled for project={context.project.id}"
        )

    # check if the linked account is configured
    linked_account = crud.linked_accounts.get_linked_account(
        context.db_session, context.project.id, function.app_id, body.linked_account_owner_id
    )
    if not linked_account:
        logger.error(
            f"linked account not found for app={function.app_id}, "
            f"project={context.project.id}, "
            f"linked_account_owner_id={body.linked_account_owner_id}"
        )
        raise LinkedAccountNotFound(
            f"app={function.app_id}, "
            f"project={context.project.id}, "
            f"linked_account_owner_id={body.linked_account_owner_id}"
        )

    if not linked_account.enabled:
        logger.error(
            f"linked account is not enabled for app={function.app_id}, "
            f"project={context.project.id}, "
            f"linked_account_owner_id={body.linked_account_owner_id}"
        )
        raise LinkedAccountDisabled(
            f"app={function.app_id}, "
            f"project={context.project.id}, "
            f"linked_account_owner_id={body.linked_account_owner_id}"
        )

    # security_credentials = cm.get_security_credentials(function.app, linked_account)

    return get_executor(function.protocol, linked_account.security_scheme).execute(
        function, body.function_input, linked_account
    )
