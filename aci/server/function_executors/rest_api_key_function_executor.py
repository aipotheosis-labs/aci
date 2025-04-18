from aci.common.enums import HttpLocation
from aci.common.exceptions import NoImplementationFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import APIKeyScheme, APIKeySchemeCredentials
from aci.server.function_executors.rest_function_executor import RestFunctionExecutor

logger = get_logger(__name__)


class RestAPIKeyFunctionExecutor(RestFunctionExecutor[APIKeyScheme, APIKeySchemeCredentials]):
    """
    Function executor for API key based REST functions.
    """

    def _inject_credentials(
        self,
        security_scheme: APIKeyScheme,
        security_credentials: APIKeySchemeCredentials,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
    ) -> None:
        """Injects api key into the request, will modify the input dictionaries in place.
        We assume the security credentials can only be in the header, query, cookie, or body.

        Args:
            security_scheme (APIKeyScheme): The security scheme.
            security_credentials (APIKeySchemeCredentials): The security credentials.
            headers (dict): The headers dictionary.
            query (dict): The query parameters dictionary.
            cookies (dict): The cookies dictionary.
            body (dict): The body dictionary.

        Examples from app.json:
        {
            "security_schemes": {
                "api_key": {
                    "in": "header",
                    "name": "X-Test-API-Key",
                }
            },
            "default_security_credentials_by_scheme": {
                "api_key": {
                    "secret_key": "default-shared-api-key"
                }
            }
        }
        """

        security_key = (
            security_credentials.secret_key
            if not security_scheme.prefix
            else f"{security_scheme.prefix} {security_credentials.secret_key}"
        )

        match security_scheme.location:
            case HttpLocation.HEADER:
                headers[security_scheme.name] = security_key
            case HttpLocation.QUERY:
                query[security_scheme.name] = security_key
            case HttpLocation.BODY:
                body[security_scheme.name] = security_key
            case HttpLocation.COOKIE:
                cookies[security_scheme.name] = security_key
            case _:
                # should never happen
                logger.error(
                    "unsupported api key location",
                    extra={"location": security_scheme.location},
                )
                raise NoImplementationFound(
                    f"unsupported api key location={security_scheme.location}"
                )
