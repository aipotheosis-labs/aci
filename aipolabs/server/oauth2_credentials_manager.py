import time

from aipolabs.common.schemas.security_scheme import OAuth2SchemeCredentials


def access_token_is_expired(oauth2_credentials: OAuth2SchemeCredentials) -> bool:
    return oauth2_credentials.expires_at < int(time.time())
