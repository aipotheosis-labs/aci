import time
from typing import Any, cast

from aipolabs.common.db.sql_models import App, LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.exceptions import NoImplementationFound
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.security_scheme import (
    APIKeySchemeCredentials,
    OAuth2SchemeCredentials,
)

logger = get_logger(__name__)


def get_security_credentials(
    app: App, linked_account: LinkedAccount
) -> APIKeySchemeCredentials | OAuth2SchemeCredentials | dict[str, Any]:
    if linked_account.security_scheme == SecurityScheme.API_KEY:
        return get_api_key_credentials(app, linked_account)
    elif linked_account.security_scheme == SecurityScheme.OAUTH2:
        return get_oauth2_credentials(app, linked_account)
    else:
        raise NoImplementationFound(f"no security credentials usable for app={app.id}")


def get_oauth2_credentials(app: App, linked_account: LinkedAccount) -> OAuth2SchemeCredentials:
    """Get OAuth2 credentials from linked account or app's default credentials.
    If the access token is expired, it will be refreshed.
    """
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
            f"no security credentials usable for app={app.id}, "
            f"security scheme={linked_account.security_scheme}, "
            f"linked account={linked_account.id}"
        )
        # TODO: check all 'NoImplementationFound' exceptions see if a more suitable exception can be used
        raise NoImplementationFound(
            f"no security credentials usable for app={app.id}, "
            f"security scheme={linked_account.security_scheme}, "
            f"linked account={linked_account.id}"
        )

    oauth2_scheme_credentials = OAuth2SchemeCredentials.model_validate(oauth2_credentials)
    return cast(OAuth2SchemeCredentials, oauth2_scheme_credentials)


# def get_new_oauth2_access_token(app: App, linked_account: LinkedAccount) -> OAuth2SchemeCredentials:
#     pass


def get_api_key_credentials(app: App, linked_account: LinkedAccount) -> APIKeySchemeCredentials:
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

    # check and use App's default security credentials if exists
    security_credentials = app.default_security_credentials_by_scheme.get(
        linked_account.security_scheme
    )
    if not security_credentials:
        logger.error(f"no default security credentials found for app={app.id}")
        raise NoImplementationFound(f"no default security credentials found for app={app.id}")
    api_key_credentials: APIKeySchemeCredentials = APIKeySchemeCredentials.model_validate(
        security_credentials
    )

    return api_key_credentials


def _access_token_is_expired(oauth2_credentials: OAuth2SchemeCredentials) -> bool:
    return oauth2_credentials.expires_at < int(time.time())
