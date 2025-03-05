from aipolabs.common.enums import Protocol, SecurityScheme
from aipolabs.common.logging import get_logger
from aipolabs.server.function_executors.base_executor import FunctionExecutor
from aipolabs.server.function_executors.rest_api_key_function_executor import (
    RestAPIKeyFunctionExecutor,
)
from aipolabs.server.function_executors.rest_oauth2_function_executor import (
    RestOAuth2FunctionExecutor,
)

logger = get_logger(__name__)


EXECUTOR_MAP: dict[Protocol, dict[SecurityScheme, type[FunctionExecutor]]] = {
    Protocol.REST: {
        SecurityScheme.API_KEY: RestAPIKeyFunctionExecutor,
        SecurityScheme.OAUTH2: RestOAuth2FunctionExecutor,
    }
}


def get_executor(protocol: Protocol, security_scheme: SecurityScheme) -> FunctionExecutor:
    return EXECUTOR_MAP[protocol][security_scheme]()


__all__ = ["FunctionExecutor", "get_executor"]
