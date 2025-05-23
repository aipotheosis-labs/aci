import base64
from typing import override

from aci.common.enums import HttpLocation
from aci.common.exceptions import NoImplementationFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import HTTPBasicScheme, HTTPBasicSchemeCredentials
from aci.server.function_executors.rest_function_executor import RestFunctionExecutor

logger = get_logger(__name__)


class RestHTTPBasicFunctionExecutor(
    RestFunctionExecutor[HTTPBasicScheme, HTTPBasicSchemeCredentials]
):
    """
    Function executor for HTTP Basic based REST functions.
    """

    @override
    def _inject_credentials(
        self,
        security_scheme: HTTPBasicScheme,
        security_credentials: HTTPBasicSchemeCredentials,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
    ) -> None:
        """Injects HTTP Basic credentials into the request, will modify the input dictionaries in place.
        We assume the security credentials can only be in the header.

        Args:
            security_scheme (HTTPBasicScheme): The security scheme.
            security_credentials (HTTPBasicSchemeCredentials): The security credentials.
            headers (dict): The headers dictionary.
            query (dict): The query parameters dictionary.
            cookies (dict): The cookies dictionary.
            body (dict): The body dictionary.

        Examples from app.json:
        {
            "security_schemes": {
                "http_basic": {
                    "location": "header",
                    "name": "Authorization",
                    "prefix": "Basic"
                }
            },
            "default_security_credentials_by_scheme": {
                "http_basic": {
                    "username": "user",
                    "password": "pass"
                }
            }
        }
        """
        if security_scheme.location != HttpLocation.HEADER:
            logger.error(
                "unsupported http basic credentials location",
                extra={"location": security_scheme.location},
            )
            raise NoImplementationFound(
                f"unsupported http basic location={security_scheme.location}"
            )

        user_pass = f"{security_credentials.username}:{security_credentials.password}"
        encoded = base64.b64encode(user_pass.encode("utf-8")).decode("utf-8")
        headers[security_scheme.name] = (
            f"{security_scheme.prefix} {encoded}" if security_scheme.prefix else encoded
        )
