from aci.common.enums import HttpLocation
from aci.common.exceptions import NoImplementationFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import OAuth2Scheme, OAuth2SchemeCredentials
from aci.server.function_executors.rest_function_executor import RestFunctionExecutor

logger = get_logger(__name__)


class RestOAuth2FunctionExecutor(RestFunctionExecutor[OAuth2Scheme, OAuth2SchemeCredentials]):
    """
    Function executor for REST OAuth2 functions.
    """

    def _inject_credentials(
        self,
        security_scheme: OAuth2Scheme,
        security_credentials: OAuth2SchemeCredentials,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
    ) -> None:
        """Injects oauth2 access token into the request"""
        logger.debug(
            "injecting oauth2 access token into the request",
            extra={
                "security_scheme": security_scheme,
                "security_credentials": security_credentials,
            },
        )
        access_token = (
            security_credentials.access_token
            if not security_scheme.prefix
            else f"{security_scheme.prefix} {security_credentials.access_token}"
        )

        match security_scheme.location:
            case HttpLocation.HEADER:
                headers[security_scheme.name] = access_token
            case HttpLocation.QUERY:
                query[security_scheme.name] = access_token
            case HttpLocation.BODY:
                body[security_scheme.name] = access_token
            case HttpLocation.COOKIE:
                cookies[security_scheme.name] = access_token
            case _:
                # should never happen
                logger.error(
                    "unsupported oauth2 credentials location",
                    extra={
                        "security_scheme": security_scheme,
                        "location": security_scheme.location,
                    },
                )
                raise NoImplementationFound(
                    f"unsupported oauth2 location={security_scheme.location}"
                )
