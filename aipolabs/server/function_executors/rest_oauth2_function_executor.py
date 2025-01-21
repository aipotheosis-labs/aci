from aipolabs.common.db.sql_models import App, LinkedAccount
from aipolabs.common.exceptions import NoImplementationFound
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.security_scheme import OAuth2SchemeCredentials
from aipolabs.server import oauth2_credentials_manager as ocm
from aipolabs.server.function_executors.rest_function_executor import (
    RestFunctionExecutor,
)

logger = get_logger(__name__)


class RestOAuth2FunctionExecutor(RestFunctionExecutor):
    """
    Function executor for REST OAuth2 functions.
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
        """Injects oauth2 access token into the request, will modify the input dictionaries in place."""

        if linked_account.security_credentials:
            logger.info(
                f"using security credentials from linked account={linked_account.id}, "
                f"security scheme={linked_account.security_scheme}"
            )
            oauth2_credentials = linked_account.security_credentials

        elif app.default_security_credentials_by_scheme.get(linked_account.security_scheme):
            logger.info(
                f"using default security credentials from app={app.name}, "
                f"security scheme={linked_account.security_scheme}, "
                f"linked account={linked_account.id}"
            )
            oauth2_credentials = app.default_security_credentials_by_scheme[
                linked_account.security_scheme
            ]
        else:
            logger.error(
                f"no security credentials usable for app={app.name}, "
                f"security scheme={linked_account.security_scheme}, "
                f"linked account={linked_account.id}"
            )
            raise NoImplementationFound(
                f"no security credentials usable for app={app.name}, "
                f"security scheme={linked_account.security_scheme}, "
                f"linked account={linked_account.id}"
            )

        oauth2_credentials = OAuth2SchemeCredentials.model_validate(oauth2_credentials)
        if ocm.access_token_is_expired(oauth2_credentials):
            logger.warning(f"access token expired for linked account={linked_account.id}")
        else:
            logger.info(f"access token is valid for linked account={linked_account.id}")
