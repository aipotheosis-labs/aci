from aipolabs.common.db.sql_models import App, LinkedAccount
from aipolabs.common.enums import HttpLocation, SecurityScheme
from aipolabs.common.exceptions import NoImplementationFound
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
)
from aipolabs.server.function_executors.rest_function_executor import (
    RestFunctionExecutor,
)

logger = get_logger(__name__)


class RestAPIKeyFunctionExecutor(RestFunctionExecutor):
    """
    Function executor for API key based REST functions.
    """

    def _inject_credentials(
        self,
        app: App,
        linked_account: LinkedAccount,
        headers: dict,
        query: dict,
        body: dict,
        cookies: dict,
    ) -> None:
        """Injects api key into the request, will modify the input dictionaries in place.
        We assume the security credentials can only be in the header, query, cookie, or body.

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
                }
            },
            "default_security_credentials_by_scheme": {
                "api_key": {
                    "secret_key": "test-api-key"
                }
            }
        }
        """
        # TODO: check if linked account has security credentials from end user before checking app's default

        # check and use App's default security credentials if exists
        security_credentials = app.default_security_credentials_by_scheme.get(
            linked_account.security_scheme
        )
        if security_credentials is None:
            logger.error(f"no default security credentials found for app={app.name}")
            raise NoImplementationFound(f"no default security credentials found for app={app.name}")
        api_key_credentials = APIKeySchemeCredentials.model_validate(security_credentials)

        # inject api key into the request based on App's security scheme configuration
        api_key_scheme = APIKeyScheme.model_validate(app.security_schemes[SecurityScheme.API_KEY])
        match api_key_scheme.location:
            case HttpLocation.HEADER:
                headers[api_key_scheme.name] = api_key_credentials.secret_key
            case HttpLocation.QUERY:
                query[api_key_scheme.name] = api_key_credentials.secret_key
            case HttpLocation.BODY:
                body[api_key_scheme.name] = api_key_credentials.secret_key
            case HttpLocation.COOKIE:
                cookies[api_key_scheme.name] = api_key_credentials.secret_key
            case _:
                # should never happen
                logger.error(
                    f"unsupported api key location={api_key_scheme.location} for app={app.name}"
                )
                raise NoImplementationFound(
                    f"unsupported api key location={api_key_scheme.location} for app={app.name}"
                )
