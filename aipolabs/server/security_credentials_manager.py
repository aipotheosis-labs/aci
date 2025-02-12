import time

from pydantic import BaseModel

from aipolabs.common.db.sql_models import App, LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.exceptions import NoImplementationFound
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aipolabs.server import oauth2

logger = get_logger(__name__)


# TODO: only pass necessary data to the functions
class SecurityCredentialsResponse(BaseModel):
    scheme: APIKeyScheme | OAuth2Scheme
    credentials: APIKeySchemeCredentials | OAuth2SchemeCredentials
    is_app_default_credentials: bool
    is_updated: bool


async def get_security_credentials(
    app: App, linked_account: LinkedAccount
) -> SecurityCredentialsResponse:
    if linked_account.security_scheme == SecurityScheme.API_KEY:
        return _get_api_key_credentials(app, linked_account)
    elif linked_account.security_scheme == SecurityScheme.OAUTH2:
        return await _get_oauth2_credentials(app, linked_account)
    else:
        error_message = (
            f"unsupported security scheme={linked_account.security_scheme.value}, app={app.name}"
        )
        logger.error(error_message)
        raise NoImplementationFound(error_message)


async def _get_oauth2_credentials(
    app: App, linked_account: LinkedAccount
) -> SecurityCredentialsResponse:
    """Get OAuth2 credentials from linked account or app's default credentials.
    If the access token is expired, it will be refreshed.
    """
    is_app_default_credentials = False
    is_updated = False
    oauth2_scheme = OAuth2Scheme.model_validate(app.security_schemes[SecurityScheme.OAUTH2])

    if linked_account.security_credentials:
        logger.info(
            f"using security credentials from linked account={linked_account.id}, "
            f"security scheme={linked_account.security_scheme}"
        )
        oauth2_credentials = linked_account.security_credentials

    elif app.default_security_credentials_by_scheme.get(linked_account.security_scheme):
        is_app_default_credentials = True
        logger.info(
            f"using default security credentials from app={app.name}, "
            f"security scheme={linked_account.security_scheme}, "
            f"linked account={linked_account.id}"
        )
        oauth2_credentials = app.default_security_credentials_by_scheme[
            linked_account.security_scheme
        ]
    else:
        logger.error(f"no security credentials usable for linked_account={linked_account.id}")
        # TODO: check all 'NoImplementationFound' exceptions see if a more suitable exception can be used
        raise NoImplementationFound(
            f"no security credentials usable for app={app.name}, "
            f"security_scheme={linked_account.security_scheme}, "
            f"linked_account_owner_id={linked_account.linked_account_owner_id}"
        )

    oauth2_scheme_credentials = OAuth2SchemeCredentials.model_validate(oauth2_credentials)
    if _access_token_is_expired(oauth2_scheme_credentials):
        logger.warning(f"access token expired for linked account={linked_account.id}")
        token_response = await _refresh_oauth2_access_token(
            app, oauth2_scheme_credentials.refresh_token
        )
        # TODO: use pydantic for validation; should we update "scope", "token_type" etc as well if
        # returned by the provider?
        oauth2_scheme_credentials = oauth2_scheme_credentials.model_copy(
            update={
                "access_token": token_response["access_token"],
                "expires_at": int(time.time()) + token_response["expires_in"],
            }
        )
        is_updated = True
    else:
        logger.info(f"access token is valid for linked account={linked_account.id}")

    return SecurityCredentialsResponse(
        scheme=oauth2_scheme,
        credentials=oauth2_scheme_credentials,
        is_app_default_credentials=is_app_default_credentials,
        is_updated=is_updated,
    )


async def _refresh_oauth2_access_token(app: App, refresh_token: str) -> dict:
    app_default_oauth2_config = OAuth2Scheme.model_validate(
        app.security_schemes[SecurityScheme.OAUTH2]
    )
    oauth2_client = oauth2.create_oauth2_client(
        name=app.name,
        client_id=app_default_oauth2_config.client_id,
        client_secret=app_default_oauth2_config.client_secret,
        scope=app_default_oauth2_config.scope,
        authorize_url=app_default_oauth2_config.authorize_url,
        access_token_url=app_default_oauth2_config.access_token_url,
        refresh_token_url=app_default_oauth2_config.refresh_token_url,
        server_metadata_url=app_default_oauth2_config.server_metadata_url,
    )
    # TODO: error handling for oauth2 methods
    token_response = await oauth2.refresh_access_token(oauth2_client, refresh_token)
    # TODO: seems the token_response contains both "expires_at" and "expires_in", in which care
    # the "expires_at" should be used. Need to double check if it's the same for "authorize_access_token" method
    # and other providers.
    logger.info(f"oauth2 access token refreshed, token_response={token_response}")

    return token_response


def _get_api_key_credentials(
    app: App, linked_account: LinkedAccount
) -> SecurityCredentialsResponse:
    """
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

    api_key_scheme = APIKeyScheme.model_validate(app.security_schemes[SecurityScheme.API_KEY])
    # check and use App's default security credentials if exists
    security_credentials = app.default_security_credentials_by_scheme.get(
        linked_account.security_scheme
    )
    if not security_credentials:
        logger.error(f"no default security credentials found for app={app.name}")
        raise NoImplementationFound(f"no default security credentials found for app={app.name}")
    api_key_credentials: APIKeySchemeCredentials = APIKeySchemeCredentials.model_validate(
        security_credentials
    )

    return SecurityCredentialsResponse(
        scheme=api_key_scheme,
        credentials=api_key_credentials,
        is_app_default_credentials=True,
        is_updated=False,
    )


# TODO: consider adding leeway for expiration
def _access_token_is_expired(oauth2_credentials: OAuth2SchemeCredentials) -> bool:
    return oauth2_credentials.expires_at < int(time.time())
