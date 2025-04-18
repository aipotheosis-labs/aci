import time

from pydantic import BaseModel

from aci.common.db.sql_models import App, LinkedAccount
from aci.common.enums import SecurityScheme
from aci.common.exceptions import NoImplementationFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
    NoAuthScheme,
    NoAuthSchemeCredentials,
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aci.server import oauth2

logger = get_logger(__name__)


# TODO: only pass necessary data to the functions
class SecurityCredentialsResponse(BaseModel):
    scheme: APIKeyScheme | OAuth2Scheme | NoAuthScheme
    credentials: APIKeySchemeCredentials | OAuth2SchemeCredentials | NoAuthSchemeCredentials
    is_app_default_credentials: bool
    is_updated: bool


async def get_security_credentials(
    app: App, linked_account: LinkedAccount
) -> SecurityCredentialsResponse:
    if linked_account.security_scheme == SecurityScheme.API_KEY:
        return _get_api_key_credentials(app, linked_account)
    elif linked_account.security_scheme == SecurityScheme.OAUTH2:
        return await _get_oauth2_credentials(app, linked_account)
    elif linked_account.security_scheme == SecurityScheme.NO_AUTH:
        return _get_no_auth_credentials(app, linked_account)
    else:
        logger.error(
            "unsupported security scheme",
            extra={
                "linked_account": linked_account.id,
                "security_scheme": linked_account.security_scheme,
                "app": app.name,
            },
        )
        raise NoImplementationFound(
            f"unsupported security scheme={linked_account.security_scheme}, app={app.name}"
        )


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
        logger.debug(
            "using linked account's security credentials",
            extra={
                "linked_account": linked_account.id,
                "security_scheme": linked_account.security_scheme,
            },
        )
        oauth2_credentials = linked_account.security_credentials

    elif app.default_security_credentials_by_scheme.get(linked_account.security_scheme):
        is_app_default_credentials = True
        logger.info(
            "using app's default security credentials",
            extra={
                "app": app.name,
                "security_scheme": linked_account.security_scheme,
                "linked_account": linked_account.id,
            },
        )
        oauth2_credentials = app.default_security_credentials_by_scheme[
            linked_account.security_scheme
        ]
    else:
        logger.error(
            "no security credentials usable",
            extra={
                "linked_account": linked_account.id,
                "security_scheme": linked_account.security_scheme,
                "app": app.name,
            },
        )
        # TODO: check all 'NoImplementationFound' exceptions see if a more suitable exception can be used
        raise NoImplementationFound(
            f"no security credentials usable for app={app.name}, "
            f"security_scheme={linked_account.security_scheme}, "
            f"linked_account_owner_id={linked_account.linked_account_owner_id}"
        )

    oauth2_scheme_credentials = OAuth2SchemeCredentials.model_validate(oauth2_credentials)
    if (
        _access_token_is_expired(oauth2_scheme_credentials)
        and oauth2_scheme_credentials.refresh_token
    ):
        logger.warning(
            "access token expired",
            extra={
                "linked_account": linked_account.id,
                "security_scheme": linked_account.security_scheme,
                "app": app.name,
            },
        )
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
        logger.debug(
            "access token is valid",
            extra={
                "linked_account": linked_account.id,
                "security_scheme": linked_account.security_scheme,
                "app": app.name,
            },
        )

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
        token_endpoint_auth_method=app_default_oauth2_config.token_endpoint_auth_method,
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
    logger.debug(
        "oauth2 access token refreshed",
        extra={"token_response": token_response, "app": app.name},
    )

    return token_response


def _get_api_key_credentials(
    app: App, linked_account: LinkedAccount
) -> SecurityCredentialsResponse:
    """
    Get API key credentials from linked account or use app's default credentials if no linked account's API key is found
    and if the app has a default shared API key.
    """
    security_credentials = (
        linked_account.security_credentials
        or app.default_security_credentials_by_scheme.get(linked_account.security_scheme)
    )

    # use "not" to cover empty dict case
    if not security_credentials:
        logger.error(
            "no api key credentials usable",
            extra={
                "app": app.name,
                "security_scheme": linked_account.security_scheme,
                "linked_account": linked_account.id,
            },
        )
        raise NoImplementationFound(
            f"no api key credentials usable for app={app.name}, "
            f"security_scheme={linked_account.security_scheme}, "
            f"linked_account_owner_id={linked_account.linked_account_owner_id}"
        )

    return SecurityCredentialsResponse(
        scheme=APIKeyScheme.model_validate(app.security_schemes[SecurityScheme.API_KEY]),
        credentials=APIKeySchemeCredentials.model_validate(security_credentials),
        is_app_default_credentials=not bool(linked_account.security_credentials),
        is_updated=False,
    )


def _get_no_auth_credentials(
    app: App, linked_account: LinkedAccount
) -> SecurityCredentialsResponse:
    """
    a somewhat no-op function, but we keep it for consistency.
    """
    return SecurityCredentialsResponse(
        scheme=NoAuthScheme.model_validate(app.security_schemes[SecurityScheme.NO_AUTH]),
        credentials=NoAuthSchemeCredentials.model_validate(linked_account.security_credentials),
        is_app_default_credentials=False,
        is_updated=False,
    )


# TODO: consider adding leeway for expiration
def _access_token_is_expired(oauth2_credentials: OAuth2SchemeCredentials) -> bool:
    if oauth2_credentials.expires_at is None:
        return False
    return oauth2_credentials.expires_at < int(time.time())
