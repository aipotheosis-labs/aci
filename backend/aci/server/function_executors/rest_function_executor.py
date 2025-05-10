from abc import abstractmethod
from typing import Any, Generic, override

import httpx
from httpx import HTTPStatusError

from aci.common.db.sql_models import Function
from aci.common.logging_setup import get_logger
from aci.common.schemas.function import FunctionExecutionResult, RestMetadata
from aci.common.schemas.security_scheme import (
    TCred,
    TScheme,
)
from aci.server.function_executors.base_executor import FunctionExecutor

logger = get_logger(__name__)


class RestFunctionExecutor(FunctionExecutor[TScheme, TCred], Generic[TScheme, TCred]):
    """
    Function executor for REST functions.
    """

    @abstractmethod
    def _inject_credentials(
        self,
        security_scheme: TScheme,
        security_credentials: TCred,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
    ) -> None:
        pass

    @override
    def _execute(
        self,
        function: Function,
        function_input: dict,
        security_scheme: TScheme,
        security_credentials: TCred,
    ) -> FunctionExecutionResult:
        # Extract parameters by location
        path: dict = function_input.get("path", {})
        query: dict = function_input.get("query", {})
        headers: dict = function_input.get("header", {})
        cookies: dict = function_input.get("cookie", {})
        body: dict = function_input.get("body", {})

        protocol_data = RestMetadata.model_validate(function.protocol_data)
        # Construct URL with path parameters
        url = f"{protocol_data.server_url}{protocol_data.path}"
        if path:
            # Replace path parameters in URL
            for path_param_name, path_param_value in path.items():
                url = url.replace(f"{{{path_param_name}}}", str(path_param_value))

        self._inject_credentials(
            security_scheme, security_credentials, headers, query, body, cookies
        )

        request = httpx.Request(
            method=protocol_data.method,
            url=url,
            params=query if query else None,
            headers=headers if headers else None,
            cookies=cookies if cookies else None,
            json=body if body else None,
        )

        logger.info(
            "executing function via raw http request",
            extra={
                "function_name": function.name,
                "method": request.method,
                "url": str(request.url),
            },
        )

        return self._send_request(request)

    def _send_request(self, request: httpx.Request) -> FunctionExecutionResult:
        # TODO: one client for all requests? cache the client? concurrency control? async client?
        # TODO: add retry
        timeout = httpx.Timeout(10.0, read=30.0)
        with httpx.Client(timeout=timeout) as client:
            try:
                response = client.send(request)
            except Exception as e:
                logger.exception(f"failed to send function execution http request, {e}")
                return FunctionExecutionResult(success=False, error=str(e))

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.exception(f"http error occurred for function execution, {e}")
                return FunctionExecutionResult(
                    success=False, error=self._get_error_message(response, e)
                )

            return FunctionExecutionResult(success=True, data=self._get_response_data(response))

    def _get_response_data(self, response: httpx.Response) -> Any:
        """Get the response data from the response.
        If the response is json, return the json data, otherwise fallback to the text.
        """
        try:
            response_data = response.json() if response.content else {}
        except Exception as e:
            logger.exception(f"error parsing function execution http response, {e}")
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
