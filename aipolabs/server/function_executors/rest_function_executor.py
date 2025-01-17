import json
from typing import Any

import httpx
from httpx import HTTPStatusError

from aipolabs.common.db.sql_models import App, Function, LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.exceptions import NoImplementationFound
from aipolabs.common.logging import create_headline, get_logger
from aipolabs.common.schemas.function import FunctionExecutionResult, RestMetadata
from aipolabs.server.function_executors.base import FunctionExecutor
from aipolabs.common.schemas.security_scheme import APIKeyScheme, APIKeySchemeCredentials
from aipolabs.common.enums import HttpLocation

logger = get_logger(__name__)


class RestFunctionExecutor(FunctionExecutor):
    """
    Function executor for REST functions.
    """

    def _execute(
        self, function: Function, function_input: dict, linked_account: LinkedAccount
    ) -> FunctionExecutionResult:
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

        # TODO: better to abstract and unify the security scheme injection
        if linked_account.security_scheme == SecurityScheme.API_KEY:
            self._inject_api_key(function.app, linked_account, headers, query, body, cookies)
        elif linked_account.security_scheme == SecurityScheme.OAUTH2:
            self._inject_access_token(function.app, linked_account, headers, query, body, cookies)
        else:
            logger.error(f"Unsupported security scheme={linked_account.security_scheme}")
            raise NoImplementationFound(
                f"Unsupported security scheme={linked_account.security_scheme}"
            )

        request = httpx.Request(
            method=protocol_data.method,
            url=url,
            params=query if query else None,
            headers=headers if headers else None,
            cookies=cookies if cookies else None,
            json=body if body else None,
        )

        # TODO: remove all print
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
                return FunctionExecutionResult(
                    success=False, error=self._get_error_message(response, e)
                )

            return FunctionExecutionResult(success=True, data=self._get_response_data(response))

    def _inject_access_token(
        self,
        app: App,
        linked_account: LinkedAccount,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
    ) -> None:
        pass

    def _inject_api_key(
        self,
        app: App,
        linked_account: LinkedAccount,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
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
                    security_credentials = APIKeySchemeCredentials.model_validate(
                        security_credentials
                    )
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
                    logger.error(
                        f"unsupported security scheme type={scheme_type} for app={app.name}"
                    )
                    continue

    def _get_response_data(self, response: httpx.Response) -> Any:
        """Get the response data from the response.
        If the response is json, return the json data, otherwise fallback to the text.
        """
        try:
            response_data = response.json() if response.content else {}
        except Exception:
            logger.exception("error parsing json response")
            response_data = response.text

        return response_data

    def _get_error_message(self, response: httpx.Response, error: HTTPStatusError) -> str:
        """Get the error message from the response or fallback to the error message from the HTTPStatusError.
        Usually the response json contains more details about the error.
        """
        try:
            return str(response.json())
        except Exception:
            return str(error)
