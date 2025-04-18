from aci.common.db.sql_models import LinkedAccount
from aci.common.enums import Protocol, SecurityScheme
from aci.common.logging_setup import get_logger
from aci.server.function_executors.base_executor import FunctionExecutor
from aci.server.function_executors.connector_function_executor import (
    ConnectorFunctionExecutor,
)
from aci.server.function_executors.rest_api_key_function_executor import (
    RestAPIKeyFunctionExecutor,
)
from aci.server.function_executors.rest_no_auth_function_executor import (
    RestNoAuthFunctionExecutor,
)
from aci.server.function_executors.rest_oauth2_function_executor import (
    RestOAuth2FunctionExecutor,
)

logger = get_logger(__name__)


def get_executor(protocol: Protocol, linked_account: LinkedAccount) -> FunctionExecutor:
    match protocol, linked_account.security_scheme:
        case Protocol.REST, SecurityScheme.API_KEY:
            return RestAPIKeyFunctionExecutor(linked_account)
        case Protocol.REST, SecurityScheme.OAUTH2:
            return RestOAuth2FunctionExecutor(linked_account)
        case Protocol.REST, SecurityScheme.NO_AUTH:
            return RestNoAuthFunctionExecutor(linked_account)
        case Protocol.CONNECTOR, _:
            return ConnectorFunctionExecutor(linked_account)
        case _:
            raise ValueError("Unsupported protocol or security scheme")


__all__ = ["FunctionExecutor", "get_executor"]
