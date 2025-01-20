from pydantic import BaseModel, Field, model_validator

from aipolabs.common.enums import HttpLocation


class APIKeyScheme(BaseModel):
    location: HttpLocation = Field(
        ...,
        description="The location of the API key in the request, e.g., 'header'",
    )
    name: str = Field(
        ...,
        description="The name of the API key in the request, e.g., 'X-Subscription-Token'",
    )


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
        description="The client ID of the OAuth2 client (provided by Aipolabs) used for the app",
    )
    client_secret: str = Field(
        ...,
        description="The client secret of the OAuth2 client (provided by Aipolabs) used for the app",
    )
    scope: str = Field(
        ...,
        description="Space separated scopes of the OAuth2 client (provided by Aipolabs) used for the app, "
        "e.g., 'openid email profile https://www.googleapis.com/auth/calendar'",
    )
    # making below fields optional because if server_metadata_url is provided, the other endpoints are usually not needed
    authorize_url: str | None = Field(
        default=None,
        description="The URL of the OAuth2 authorization server, e.g., 'https://accounts.google.com/o/oauth2/auth'",
    )
    access_token_url: str | None = Field(
        default=None,
        description="The URL of the OAuth2 access token server, e.g., 'https://oauth2.googleapis.com/token'",
    )
    refresh_token_url: str | None = Field(
        default=None,
        description="The URL of the OAuth2 refresh token server, e.g., 'https://oauth2.googleapis.com/token'",
    )
    server_metadata_url: str | None = Field(
        default=None,
        description="The URL of the OAuth2 server metadata/discovery doc, e.g., 'https://accounts.google.com/.well-known/openid-configuration'",
    )

    # validation: if server_metadata_url is None, the other urls must NOT be None
    @model_validator(mode="after")
    def validate_urls(self) -> "OAuth2Scheme":
        if self.server_metadata_url is None:
            if (
                self.authorize_url is None
                or self.access_token_url is None
                or self.refresh_token_url is None
            ):
                raise ValueError(
                    "If server_metadata_url is not provided, the other endpoints must be provided"
                )
        return self


# TODO: add pydantic model for other security schemes (e.g., HTTP Basic, HTTP Bearer)


class APIKeySchemeCredentials(BaseModel):
    """
    Credentials for API key scheme
    Technically this can just be a string, but we use JSON to store the credentials in the database
    for consistency and flexibility.
    """

    # here weuse a different name 'secret_key' to avoid confusion with SecurityScheme.API_KEY, and for
    # potential unification with http bearer scheme
    # TODO: consider having a list of secret_keys for round robin http requests
    secret_key: str


class OAuth2SchemeCredentials(BaseModel):
    """Credentials for OAuth2 scheme"""

    # TODO: some of them might be optional (e.g., refresh_token, scope, expires_in,
    # refresh_token_expires_in) and not provided by the OAuth2 provider
    # we should handle None or provide default values
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    refresh_token: str
