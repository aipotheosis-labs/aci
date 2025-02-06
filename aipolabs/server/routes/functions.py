import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from aipolabs.common import processor
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Function
from aipolabs.common.enums import Visibility
from aipolabs.common.exceptions import (
    AgentNotFound,
    AppConfigurationDisabled,
    AppConfigurationNotFound,
    CustomInstructionViolation,
    FunctionNotFound,
    LinkedAccountDisabled,
    LinkedAccountNotFound,
)
from aipolabs.common.filter import filter_function_call
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
from aipolabs.server import security_credentials_manager as scm
from aipolabs.server.function_executors import get_executor
from aipolabs.server.security_credentials_manager import SecurityCredentialsResponse

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

    # check if the linked account status (configured, enabled, etc.)
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

    security_credentials_response: SecurityCredentialsResponse = await scm.get_security_credentials(
        function.app, linked_account
    )
    # if the security credentials are updated during fetch (e.g, access token refreshed), we need to write back
    # to the database with the updated credentials, either to linked account or app configuration depending
    # on if the default or linked account credentials were used
    # TODO: this is an unnnecessary unification? Technically the update only apply to oauth2 based
    # credentials. Might need to structure differently to have a less generic solution (but without adding
    # more complexity to the logic). It almost smells like an indicator to break down to microservices and/or
    # use a message queue like kafka for async/downstream updates.
    logger.info(
        f"security_credentials_response={json.dumps(security_credentials_response.model_dump(mode='json'), indent=2)}"
    )
    if security_credentials_response.is_updated:
        if security_credentials_response.is_app_default_credentials:
            crud.apps.update_app_default_security_credentials(
                context.db_session,
                function.app,
                linked_account.security_scheme,
                security_credentials_response.credentials.model_dump(),
            )
        else:
            crud.linked_accounts.update_linked_account(
                context.db_session,
                linked_account,
                security_credentials=security_credentials_response.credentials.model_dump(),
            )
        context.db_session.commit()

    agent = crud.projects.get_agent_by_api_key_id(context.db_session, context.api_key_id)
    if not agent:
        logger.error(f"agent not found for api_key_id={context.api_key_id}")
        raise AgentNotFound(f"agent not found for api_key_id={context.api_key_id}")

    if str(function.app_id) in agent.custom_instructions.keys():
        filter_result = filter_function_call(
            openai_service,
            function,
            body.function_input,
            agent.custom_instructions[str(function.app_id)],
        )
        logger.info(f"Filter Result: {filter_result}")
        # Filter has failed
        if not filter_result.success:
            raise CustomInstructionViolation(
                f"Function execution for function: {function.name}\n with description:"
                f"{function.description}, \nparameters: {function.parameters} \nand input: "
                f"{body.function_input} \nhas been rejected because of rule: "
                f"{agent.custom_instructions[str(function.app_id)]} \nand the reason from"
                f"the filter is: {filter_result.reason}"
            )

    function_executor = get_executor(function.protocol, linked_account.security_scheme)

    # TODO: async calls?
    return function_executor.execute(
        function,
        body.function_input,
        security_credentials_response.scheme,
        security_credentials_response.credentials,
    )
