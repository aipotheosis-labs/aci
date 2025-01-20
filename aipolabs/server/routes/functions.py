import json
from typing import Annotated, Any
from uuid import UUID

import httpx
import jsonschema
from fastapi import APIRouter, Depends, Query
from httpx import HTTPStatusError

from aipolabs.common import processor
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Function
from aipolabs.common.enums import HttpLocation, Protocol, SecurityScheme, Visibility
from aipolabs.common.exceptions import (
    FunctionNotFound,
    InvalidFunctionInput,
    UnexpectedException,
)
from aipolabs.common.logging import create_headline, get_logger
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
    RestMetadata,
)
from aipolabs.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
)
from aipolabs.server import config
from aipolabs.server import dependencies as deps

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
    # - when clients search for functions, if the app of the functions is not configured, should the functions be discoverable?
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

    return _execute(function, body.function_input)


# TODO: allow local code execution override by using AppBase.execute() e.g.,:
# app_factory = AppFactory()
# app_instance: AppBase = app_factory.get_app_instance(function_name)
# app_instance.validate_input(function.parameters, function_execution_params.function_input)
# return app_instance.execute(function_name, function_execution_params.function_input)
def _execute(function: Function, function_input: dict) -> FunctionExecutionResult:
    # validate user input against the visible parameters
    try:
        logger.info(f"validating function input for {function.name}")
        jsonschema.validate(
            instance=function_input,
            schema=processor.filter_visible_properties(function.parameters),
        )
    except jsonschema.ValidationError as e:
        logger.exception("failed to validate function input")
        raise InvalidFunctionInput(e.message)

    logger.info(f"function_input before injecting defaults: {json.dumps(function_input)}")

    # inject non-visible defaults, note that should pass the original parameters schema not just visible ones
    function_input = processor.inject_required_but_invisible_defaults(
        function.parameters, function_input
    )
    logger.info(f"function_input after injecting defaults: {json.dumps(function_input)}")

    if function.protocol == Protocol.REST:
        # remove None values from the input
        # TODO: better way to remove None values? and if it's ok to remove all of them?
        function_input = processor.remove_none_values(function_input)
        # Extract parameters by location
        path = function_input.get("path", {})
        query = function_input.get("query", {})
        headers = function_input.get("header", {})
        cookies = function_input.get("cookie", {})
        body = function_input.get("body", {})

        protocol_data = RestMetadata.model_validate(function.protocol_data)
        # Construct URL with path parameters
        url = f"{protocol_data.server_url}{protocol_data.path}"
        if path:
            # Replace path parameters in URL
            for path_param_name, path_param_value in path.items():
                url = url.replace(f"{{{path_param_name}}}", str(path_param_value))

        _inject_security_credentials(function.app, headers, query, body, cookies)

        # Create request object
        request = httpx.Request(
            method=protocol_data.method,
            url=url,
            params=query if query else None,
            headers=headers if headers else None,
            cookies=cookies if cookies else None,
            json=body if body else None,
        )

        # TODO: remove all print ?
        print(create_headline("FUNCTION EXECUTION HTTP REQUEST"))

        logger.info(
            f"Method: {request.method}\n"
            f"URL: {request.url}\n"
            f"Headers: {json.dumps(dict(request.headers))}\n"
            f"Body: {json.dumps(json.loads(request.content)) if request.content else None}\n"
        )

        # TODO: one client for all requests?
        with httpx.Client() as client:
            try:
                response = client.send(request)
            except Exception as e:
                logger.exception("failed to send request")
                return FunctionExecutionResult(success=False, error=str(e))

            # Raise an error for bad responses
            try:
                response.raise_for_status()
            except HTTPStatusError as e:
                logger.exception("http error occurred")
                return FunctionExecutionResult(success=False, error=_get_error_message(response, e))

            return FunctionExecutionResult(success=True, data=_get_response_data(response))
    else:
        # should never happen
        logger.error(f"unsupported protocol for function={function.name}")
        raise UnexpectedException(f"unsupported protocol for function={function.name}")


def _inject_security_credentials(
    app: App, headers: dict, query: dict, body: dict, cookies: dict
) -> None:
    """Injects authentication tokens based on the app's security schemes.

    We assume the security credentials can only be in the header, query, cookie, or body.
    Modifies the input dictionaries in place.

    # TODO: the right way for injecting security credentials is to get from the linked account first,
    # and if not found, then use the app's default

    Args:
        app (App): The application model containing security schemes and authentication info.
        query (dict): The query parameters dictionary.
        headers (dict): The headers dictionary.
        cookies (dict): The cookies dictionary.
        body (dict): The body dictionary.

    Examples from app.json:
    {
        "security_schemes": {
            "api_key": {
                "in": "header",
                "name": "X-Test-API-Key",
                "default": ["test-api-key"]
            }
        },
        "default_security_credentials_by_scheme": {
            "api_key": {
                "secret_key": "test-api-key"
            }
        }
    }
    """
    for scheme_type, security_credentials in app.default_security_credentials_by_scheme.items():
        match scheme_type:
            case SecurityScheme.API_KEY:
                api_key_scheme = APIKeyScheme.model_validate(app.security_schemes[scheme_type])
                security_credentials = APIKeySchemeCredentials.model_validate(security_credentials)
                match api_key_scheme.location:
                    case HttpLocation.HEADER:
                        headers[api_key_scheme.name] = security_credentials.secret_key
                        break
                    case HttpLocation.QUERY:
                        query[api_key_scheme.name] = security_credentials.secret_key
                        break
                    case HttpLocation.BODY:
                        body[api_key_scheme.name] = security_credentials.secret_key
                        break
                    case HttpLocation.COOKIE:
                        cookies[api_key_scheme.name] = security_credentials.secret_key
                        break
                    case _:
                        logger.error(
                            f"unsupported api key location={api_key_scheme.location} for app={app.name}"
                        )
                        continue
            case _:
                logger.error(f"unsupported security scheme type={scheme_type} for app={app.name}")
                continue


def _get_response_data(response: httpx.Response) -> Any:
    """Get the response data from the response.
    If the response is json, return the json data, otherwise fallback to the text.
    """
    try:
        response_data = response.json() if response.content else {}
    except Exception:
        logger.exception("error parsing json response")
        response_data = response.text

    return response_data


def _get_error_message(response: httpx.Response, error: HTTPStatusError) -> str:
    """Get the error message from the response or fallback to the error message from the HTTPStatusError.
    Usually the response json contains more details about the error.
    """
    try:
        return str(response.json())
    except Exception:
        return str(error)
