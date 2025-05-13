from typing import Literal, TypeVar

from pydantic import BaseModel, Field

from aci.common.enums import HttpLocation


class APIKeyScheme(BaseModel):
    location: HttpLocation = Field(
        ...,
        description="The location of the API key in the request, e.g., 'header'",
    )
    name: str = Field(
        ...,
        description="The name of the API key in the request, e.g., 'X-Subscription-Token'",
    )
    prefix: str | None = Field(
        default=None,
        description="The prefix of the API key in the request, e.g., 'Bearer'. If None, no prefix will be used.",
    )


# NOTE: not necessary but for the sake of consistency and future use
class APIKeySchemePublic(BaseModel):
    pass


class OAuth2Scheme(BaseModel):
    # TODO: consider providing a default value for in_, name, prefix as they are usually the same for most apps
    location: HttpLocation = Field(
        ...,
        description="The location of the OAuth2 access token in the request, e.g., 'header'",
    )
    name: str = Field(
        ...,
        description="The name of the OAuth2 access token in the request, e.g., 'Authorization'",
    )
    prefix: str = Field(
        ...,
        description="The prefix of the OAuth2 access token in the request, e.g., 'Bearer'",
    )
    client_id: str = Field(
        ...,
        min_length=1,
        description="The client ID of the OAuth2 client (provided by ACI) used for the app",
    )
    client_secret: str = Field(
        ...,
        min_length=1,
        description="The client secret of the OAuth2 client (provided by ACI) used for the app",
    )
    scope: str = Field(
        ...,
        description="Space separated scopes of the OAuth2 client (provided by ACI) used for the app, "
        "e.g., 'openid email profile https://www.googleapis.com/auth/calendar'",
    )
    authorize_url: str = Field(
        ...,
        description="The URL of the OAuth2 authorization server, e.g., 'https://accounts.google.com/o/oauth2/v2/auth'",
    )
    access_token_url: str = Field(
        ...,
        description="The URL of the OAuth2 access token server, e.g., 'https://oauth2.googleapis.com/token'",
    )
    refresh_token_url: str = Field(
        ...,
        description="The URL of the OAuth2 refresh token server, e.g., 'https://oauth2.googleapis.com/token'",
    )
    token_endpoint_auth_method: Literal["client_secret_basic", "client_secret_post"] | None = Field(
        default=None,
        description="The authentication method for the OAuth2 token endpoint, e.g., 'client_secret_post' "
        "for some providers that require client_id/client_secret to be sent in the body of the token request, like Hubspot",
    )


# NOTE: need to show these fields for custom oauth2 app feature.
class OAuth2SchemePublic(BaseModel):
    # user needs to know the scope to set in their own oauth2 app.
    scope: str = Field(
        ...,
        description="Space separated scopes of the OAuth2 client used for the app, "
        "e.g., 'openid email profile https://www.googleapis.com/auth/calendar'",
    )


class OAuth2SchemeOverride(BaseModel):
    """
    Fields that are allowed to be overridden by the user.
    """

    client_id: str = Field(
        ...,
        min_length=1,
        description="The client ID of the OAuth2 client used for the app",
    )
    client_secret: str = Field(
        ...,
        min_length=1,
        description="The client secret of the OAuth2 client used for the app",
    )
    # TODO: will support "scope" and "redirect_uri" in the future, both will be optional


class NoAuthScheme(BaseModel, extra="forbid"):
    """
    model for security scheme that has no authentication.
    For now it only allows an empty dict, this is clearer and less ambiguous than using {} or None directly.
    We could also add some fields as metadata in the future if needed.
    """

    pass


# NOTE: not necessary but for the sake of consistency and future use
class NoAuthSchemePublic(BaseModel):
    pass


class APIKeySchemeCredentials(BaseModel):
    """
    Credentials for API key scheme
    Technically this can just be a string, but we use JSON to store the credentials in the database
    for consistency and flexibility.
    """

    # here we use a different name 'secret_key' to avoid confusion with SecurityScheme.API_KEY, and for
    # potential unification with http bearer scheme
    # TODO: consider allowing a list of secret_keys for round robin http requests
    secret_key: str


class OAuth2SchemeCredentials(BaseModel):
    """Credentials for OAuth2 scheme"""

    # We need to store client_id and client_secret as part of the credentials because oauth2 client can
    # change any time for a particular App Configuration. (e.g., user provided custom oauth2 app, or we changed
    # our default oauth2 app). In which case, we still want the existing linked accounts to work. (refresh token)
    client_id: str
    client_secret: str
    # Technically we don't need to store scope, but can be useful if we know which accounts are not up to date
    # with current App/ App Configuration's oauth2 scopes and to let user know.
    scope: str
    access_token: str
    token_type: str | None = None
    expires_at: int | None = None
    refresh_token: str | None = None
    raw_token_response: dict | None = None


class NoAuthSchemeCredentials(BaseModel, extra="forbid"):
    """
    Credentials for no auth scheme
    For now it only allows an empty dict, this is clearer and less ambiguous than using {} or None directly.
    We could also add some fields as metadata in the future if needed.
    # TODO: there is some ambiguity with "no auth" and "use app's default credentials", needs a refactor.
    """

    pass


class SecuritySchemesPublic(BaseModel):
    """
    scheme_type -> scheme with sensitive information removed
    """

    api_key: APIKeySchemePublic | None = None
    oauth2: OAuth2SchemePublic | None = None
    no_auth: NoAuthSchemePublic | None = None


class SecuritySchemeOverrides(BaseModel, extra="forbid"):
    """
    Allowed security scheme overrides
    NOTE: for now we only support oauth2 overrides (because nothing is overridable for api_key and no_auth)
    """

    oauth2: OAuth2SchemeOverride | None = None


TScheme = TypeVar("TScheme", APIKeyScheme, OAuth2Scheme, NoAuthScheme)
TCred = TypeVar("TCred", APIKeySchemeCredentials, OAuth2SchemeCredentials, NoAuthSchemeCredentials)
