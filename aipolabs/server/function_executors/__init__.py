from aipolabs.common.enums import Protocol, SecurityScheme
from aipolabs.common.exceptions import NoImplementationFound
from aipolabs.common.logging import get_logger
from aipolabs.server.function_executors.base_executor import FunctionExecutor
from aipolabs.server.function_executors.rest_api_key_function_executor import (
    RestAPIKeyFunctionExecutor,
)
from aipolabs.server.function_executors.rest_oauth2_function_executor import (
    RestOAuth2FunctionExecutor,
)

logger = get_logger(__name__)


def get_executor(protocol: Protocol, security_scheme: SecurityScheme) -> FunctionExecutor:
    if protocol == Protocol.REST:
        if security_scheme == SecurityScheme.API_KEY:
            return RestAPIKeyFunctionExecutor()
        elif security_scheme == SecurityScheme.OAUTH2:
            return RestOAuth2FunctionExecutor()
        else:
            logger.error(f"Unsupported security scheme={security_scheme} for protocol={protocol}")
            raise NoImplementationFound(
                f"Unsupported security scheme={security_scheme} for protocol={protocol}"
            )
    else:
        logger.error(f"Unsupported protocol={protocol}")  # type: ignore[unreachable]
        raise NoImplementationFound(f"Unsupported protocol={protocol}")


__all__ = ["FunctionExecutor", "get_executor"]
