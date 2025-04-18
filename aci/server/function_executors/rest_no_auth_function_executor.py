from typing import override

from aci.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aci.server.function_executors.rest_function_executor import RestFunctionExecutor


class RestNoAuthFunctionExecutor(RestFunctionExecutor[NoAuthScheme, NoAuthSchemeCredentials]):
    """
    Function executor for REST functions that don't require authentication.
    """

    @override
    def _inject_credentials(
        self,
        security_scheme: NoAuthScheme,
        security_credentials: NoAuthSchemeCredentials,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
    ) -> None:
        # No authentication required, so nothing to inject
        pass
