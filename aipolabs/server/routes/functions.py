from typing import Annotated

from fastapi import APIRouter, Depends, Query
from openai import OpenAI

from aipolabs.common import processor
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Function
from aipolabs.common.embeddings import generate_embedding
from aipolabs.common.enums import FunctionDefinitionFormat, Visibility
from aipolabs.common.exceptions import (
    AppConfigurationDisabled,
    AppConfigurationNotFound,
    AppNotAllowedForThisAgent,
    FunctionNotFound,
    InvalidFunctionDefinitionFormat,
    LinkedAccountDisabled,
    LinkedAccountNotFound,
)
from aipolabs.common.logging_setup import get_logger
from aipolabs.common.schemas.function import (
    AnthropicFunctionDefinition,
    BasicFunctionDefinition,
    FunctionDetails,
    FunctionExecute,
    FunctionExecutionResult,
    FunctionsList,
    FunctionsSearch,
    OpenAIFunction,
    OpenAIFunctionDefinition,
)
from aipolabs.server import config, custom_instructions
from aipolabs.server import dependencies as deps
from aipolabs.server import security_credentials_manager as scm
from aipolabs.server.function_executors import get_executor
from aipolabs.server.security_credentials_manager import SecurityCredentialsResponse

router = APIRouter()
logger = get_logger(__name__)
# TODO: will this be a bottleneck and problem if high concurrent requests from users?
# TODO: should probably be a singleton and inject into routes, shared access with Apps route
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)


@router.get("", response_model=list[FunctionDetails])
async def list_functions(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[FunctionsList, Query()],
) -> list[Function]:
    """Get a list of functions and their details. Sorted by function name."""
    logger.info(
        "list functions",
        extra={"function_list": query_params.model_dump(exclude_none=True)},
    )
    return crud.functions.get_functions(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        query_params.app_names,
        query_params.limit,
        query_params.offset,
    )


@router.get("/search", response_model_exclude_none=True)
async def search_functions(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[FunctionsSearch, Query()],
) -> list[BasicFunctionDefinition | OpenAIFunctionDefinition | AnthropicFunctionDefinition]:
    """
    Returns the basic information of a list of functions.
    """
    # TODO: currently the search is done across all apps, we might want to add flags to account for below scenarios:
    # - when clients search for functions, if the app of the functions is configured but disabled by client, should the functions be discoverable?
    logger.info(
        "search functions",
        extra={"function_search": query_params.model_dump(exclude_none=True)},
    )
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
        "generated intent embedding",
        extra={"intent": query_params.intent, "intent_embedding": intent_embedding},
    )

    # get the apps to filter (or not) based on the allowed_apps_only and app_names query params
    if query_params.allowed_apps_only:
        if query_params.app_names is None:
            apps_to_filter = context.agent.allowed_apps
        else:
            apps_to_filter = list(set(query_params.app_names) & set(context.agent.allowed_apps))
    else:
        if query_params.app_names is None:
            apps_to_filter = None
        else:
            apps_to_filter = query_params.app_names

    functions = crud.functions.search_functions(
        context.db_session,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
        apps_to_filter,
        intent_embedding,
        query_params.limit,
        query_params.offset,
    )
    logger.info(
        "search functions result",
        extra={"function_names": [function.name for function in functions]},
    )
    function_definitions = [
        _get_function_definition(function, query_params.format) for function in functions
    ]

    return function_definitions


# TODO: have "structured_outputs" flag ("structured_outputs_if_possible") to support openai's structured outputs function calling?
# which need "strict: true" and only support a subset of json schema and a bunch of other restrictions like "All fields must be required"
# If you turn on Structured Outputs by supplying strict: true and call the API with an unsupported JSON Schema, you will receive an error.
# TODO: client sdk can use pydantic to validate model output for parameters used for function execution
# TODO: "flatten" flag to make sure nested parameters are flattened?
@router.get(
    "/{function_name}/definition",
    response_model_exclude_none=True,  # having this to exclude "strict" field in openai's function definition if not set
)
async def get_function_definition(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    function_name: str,
    format: FunctionDefinitionFormat = Query(  # noqa: B008 # TODO: need to fix this later
        default=FunctionDefinitionFormat.OPENAI,
        description="The format to use for the function definition (e.g., 'openai' or 'anthropic'). "
        "There is also a 'basic' format that only returns name and description.",
    ),
) -> OpenAIFunctionDefinition | AnthropicFunctionDefinition | BasicFunctionDefinition:
    """
    Return the function definition that can be used directly by LLM.
    The actual content depends on the FunctionDefinitionFormat and the function itself.
    """
    logger.info(
        "get function definition",
        extra={
            "function_name": function_name,
            "format": format,
        },
    )
    function: Function | None = crud.functions.get_function(
        context.db_session,
        function_name,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )
    if not function:
        logger.error(
            "failed to get function definition, function not found",
            extra={"function_name": function_name},
        )
        raise FunctionNotFound(f"function={function_name} not found")

    function_definition = _get_function_definition(function, format)

    logger.info(
        "function definition to return",
        extra={
            "format": format,
            "function_name": function_name,
            "function_definition": function_definition.model_dump(exclude_none=True),
        },
    )
    return function_definition


# TODO: is there any way to abstract and generalize the checks and validations
# (enabled, configured, accessible, etc.)?
@router.post(
    "/{function_name}/execute",
    response_model=FunctionExecutionResult,
    response_model_exclude_none=True,
)
async def execute(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    function_name: str,
    body: FunctionExecute,
) -> FunctionExecutionResult:
    # Fetch function definition
    logger.info(
        "execute function",
        extra={
            "function_name": function_name,
            "function_execute": body.model_dump(exclude_none=True),
        },
    )
    function = crud.functions.get_function(
        context.db_session,
        function_name,
        context.project.visibility_access == Visibility.PUBLIC,
        True,
    )
    if not function:
        logger.error(
            "failed to execute function, function not found",
            extra={
                "function_name": function_name,
                "linked_account_owner_id": body.linked_account_owner_id,
            },
        )
        raise FunctionNotFound(f"function={function_name} not found")

    # check if the App (that this function belongs to) is configured
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, function.app.name
    )
    if not app_configuration:
        logger.error(
            "failed to execute function, app configuration not found",
            extra={
                "function_name": function_name,
                "app_name": function.app.name,
            },
        )
        raise AppConfigurationNotFound(
            f"configuration for app={function.app.name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{function.app.name}"
        )

    # check if user has disabled the app configuration
    if not app_configuration.enabled:
        logger.error(
            "failed to execute function, app configuration is disabled",
            extra={
                "function_name": function_name,
                "app_name": function.app.name,
                "app_configuration_id": app_configuration.id,
            },
        )
        raise AppConfigurationDisabled(
            f"configuration for app={function.app.name} is disabled, please enable the app first {config.DEV_PORTAL_URL}/appconfig/{function.app.name}"
        )

    # check if the function is allowed to be executed by the agent
    if function.app.name not in context.agent.allowed_apps:
        logger.error(
            "failed to execute function, App not allowed to be used by this agent",
            extra={
                "function_name": function_name,
                "app_name": function.app.name,
                "agent_id": context.agent.id,
            },
        )
        raise AppNotAllowedForThisAgent(
            f"App={function.app.name} that this function belongs to is not allowed to be used by agent={context.agent.name}"
        )

    # check if the linked account status (configured, enabled, etc.)
    linked_account = crud.linked_accounts.get_linked_account(
        context.db_session,
        context.project.id,
        function.app.name,
        body.linked_account_owner_id,
    )
    if not linked_account:
        logger.error(
            "failed to execute function, linked account not found",
            extra={
                "function_name": function_name,
                "app_name": function.app.name,
                "linked_account_owner_id": body.linked_account_owner_id,
            },
        )
        raise LinkedAccountNotFound(
            f"linked account with linked_account_owner_id={body.linked_account_owner_id} not found for app={function.app.name},"
            f"please link the account for this app here: {config.DEV_PORTAL_URL}/appconfig/{function.app.name}"
        )

    if not linked_account.enabled:
        logger.error(
            "failed to execute function, linked account is disabled",
            extra={
                "function_name": function_name,
                "app_name": function.app.name,
                "linked_account_owner_id": body.linked_account_owner_id,
                "linked_account_id": linked_account.id,
            },
        )
        raise LinkedAccountDisabled(
            f"linked account with linked_account_owner_id={body.linked_account_owner_id} is disabled for app={function.app.name},"
            f"please enable the account for this app here: {config.DEV_PORTAL_URL}/appconfig/{function.app.name}"
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
        "fetched security credentials for function execution",
        extra={
            "function_name": function_name,
            "app_name": function.app.name,
            "linked_account_owner_id": body.linked_account_owner_id,
            "linked_account_id": linked_account.id,
            "scheme": security_credentials_response.scheme.model_dump(exclude_none=True),
            "is_app_default_credentials": security_credentials_response.is_app_default_credentials,
            "is_updated": security_credentials_response.is_updated,
        },
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
            crud.linked_accounts.update_linked_account_credentials(
                context.db_session,
                linked_account,
                security_credentials=security_credentials_response.credentials,
            )
        context.db_session.commit()

    custom_instructions.check_for_violation(
        openai_client,
        function,
        body.function_input,
        context.agent.custom_instructions,
    )

    function_executor = get_executor(function.protocol, linked_account)
    logger.info(
        "instantiated function executor",
        extra={"function_name": function_name, "function_executor": type(function_executor)},
    )

    # TODO: async calls?
    execution_result = function_executor.execute(
        function,
        body.function_input,
        security_credentials_response.scheme,
        security_credentials_response.credentials,
    )
    if not execution_result.success:
        logger.error(
            "function execution result error",
            extra={
                "function_name": function_name,
                "error": execution_result.error,
            },
        )
    return execution_result


def _get_function_definition(
    function: Function, format: FunctionDefinitionFormat
) -> BasicFunctionDefinition | OpenAIFunctionDefinition | AnthropicFunctionDefinition:
    match format:
        case FunctionDefinitionFormat.BASIC:
            return BasicFunctionDefinition(
                name=function.name,
                description=function.description,
            )
        case FunctionDefinitionFormat.OPENAI:
            return OpenAIFunctionDefinition(
                function=OpenAIFunction(
                    name=function.name,
                    description=function.description,
                    parameters=processor.filter_visible_properties(function.parameters),
                )
            )
        case FunctionDefinitionFormat.ANTHROPIC:
            return AnthropicFunctionDefinition(
                name=function.name,
                description=function.description,
                input_schema=processor.filter_visible_properties(function.parameters),
            )
        case _:
            raise InvalidFunctionDefinitionFormat(f"Invalid format: {format}")
