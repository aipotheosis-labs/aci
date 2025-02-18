from typing import Any, cast

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from fastapi import Request
from starlette.responses import RedirectResponse

from aipolabs.common.exceptions import LinkedAccountOAuth2Error
from aipolabs.common.logging import get_logger

logger = get_logger(__name__)


"""
Mostly a wrapper around authlib oauth2 features.
Having a wrapper because for some function we need do some special overrides.
And potentially easier for testing and refactoring if later we want to switch to a different oauth2 library.
"""

# TODO: oauth2 related code smells bad


def create_oauth2_client(
    name: str,
    client_id: str,
    client_secret: str,
    scope: str,
    prompt: str = "consent",
    code_challenge_method: str = "S256",
    access_type: str = "offline",
    token_endpoint_auth_method: str | None = None,
    authorize_url: str | None = None,
    access_token_url: str | None = None,
    refresh_token_url: str | None = None,
    server_metadata_url: str | None = None,
) -> StarletteOAuth2App:
    """
    Create an OAuth2 client for the given app.
    """
    oauth_client = OAuth().register(
        name=name,
        client_id=client_id,
        client_secret=client_secret,
        client_kwargs={
            "scope": scope,
            "prompt": prompt,
            "code_challenge_method": code_challenge_method,
            "token_endpoint_auth_method": token_endpoint_auth_method,
        },
        # Note: usually if server_metadata_url (e.g., google's discovery doc https://accounts.google.com/.well-known/openid-configuration)
        # is provided, the other endpoints are not needed.
        authorize_url=authorize_url,
        authorize_params={"access_type": access_type},
        access_token_url=access_token_url,
        refresh_token_url=refresh_token_url,
        server_metadata_url=server_metadata_url,
    )
    return cast(StarletteOAuth2App, oauth_client)


async def authorize_redirect(
    oauth2_client: StarletteOAuth2App, request: Request, redirect_uri: str
) -> RedirectResponse:
    return cast(RedirectResponse, await oauth2_client.authorize_redirect(request, redirect_uri))


async def create_authorization_url(oauth2_client: StarletteOAuth2App, redirect_uri: str) -> dict:
    return cast(dict, await oauth2_client.create_authorization_url(redirect_uri))


async def authorize_access_token(
    oauth2_client: StarletteOAuth2App,
    request: Request,
    **kwargs: Any,
) -> dict:
    return cast(dict, await oauth2_client.authorize_access_token(request, **kwargs))


async def refresh_access_token(oauth2_client: StarletteOAuth2App, refresh_token: str) -> dict:
    return cast(
        dict,
        await oauth2_client.fetch_access_token(
            grant_type="refresh_token", refresh_token=refresh_token
        ),
    )


async def authorize_access_token_without_browser_session(
    oauth2_client: StarletteOAuth2App,
    request: Request,
    redirect_uri: str,
    code_verifier: str,
    nonce: str | None = None,
    **kwargs: Any,
) -> dict:
    """
    This is a modified version of the authorize_access_token method in authlib/integrations/starlette_client/apps.py
    This is to bypass a need of browser session for oauth2 flow
    """
    logger.debug(
        "authorizing access token without browser session",
        extra={"redirect_uri": redirect_uri, "code_verifier": code_verifier},
    )
    error = request.query_params.get("error")
    if error:
        description = request.query_params.get("error_description")
        error_msg = f"account linking failed due to OAuth2 error from provider. error={error}"
        if description:
            error_msg += f", error_description={description}"
        logger.error(error_msg)
        raise LinkedAccountOAuth2Error(error_msg)

    params = {
        "code": request.query_params.get("code"),
        "state": request.query_params.get("state"),
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    claims_options = kwargs.pop("claims_options", None)
    logger.debug(
        "fetching access token",
        extra=params,
    )
    token = cast(dict, await oauth2_client.fetch_access_token(**params, **kwargs))

    if "id_token" in token and nonce:
        userinfo = await oauth2_client.parse_id_token(
            token, nonce=nonce, claims_options=claims_options
        )
        token["userinfo"] = userinfo
    return token
