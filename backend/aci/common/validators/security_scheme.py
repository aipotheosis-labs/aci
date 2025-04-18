from aci.common.enums import SecurityScheme
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    APIKeySchemeCredentials,
    NoAuthSchemeCredentials,
    OAuth2SchemeCredentials,
)

logger = get_logger(__name__)


def validate_scheme_and_credentials_type_match(
    security_scheme: SecurityScheme,
    security_credentials: OAuth2SchemeCredentials
    | APIKeySchemeCredentials
    | NoAuthSchemeCredentials,
) -> None:
    scheme_to_credentials = {
        SecurityScheme.OAUTH2: OAuth2SchemeCredentials,
        SecurityScheme.API_KEY: APIKeySchemeCredentials,
        SecurityScheme.NO_AUTH: NoAuthSchemeCredentials,
    }

    expected_type = scheme_to_credentials.get(security_scheme)
    if expected_type is None:
        logger.error(
            "Unsupported security scheme",
            extra={"scheme": security_scheme, "credentials_type": type(security_credentials)},
        )
        raise ValueError(f"Unsupported security scheme: {security_scheme}")

    if not isinstance(security_credentials, expected_type):
        logger.error(
            "Scheme and credentials type mismatch",
            extra={"scheme": security_scheme, "credentials_type": type(security_credentials)},
        )
        raise ValueError(
            f"Invalid security credentials type: {type(security_credentials)} for scheme: {security_scheme}"
        )
