import time
from typing import Any, cast

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from fastapi import Request
from starlette.responses import RedirectResponse

from aci.common.exceptions import LinkedAccountOAuth2Error
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import OAuth2SchemeCredentials

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


def parse_oauth2_security_credentials(
    app_name: str, token_response: dict
) -> OAuth2SchemeCredentials:
    """
    Parse OAuth2SchemeCredentials from token response with app-specific handling.

    Args:
        app_name: Name of the app/provider (e.g., "SLACK", "GOOGLE")
        token_response: OAuth2 token response from provider

    Returns:
        OAuth2SchemeCredentials with appropriate fields set
    """
    if app_name == "SLACK":
        authed_user = token_response.get("authed_user", {})
        if not authed_user or "access_token" not in authed_user:
            logger.error(f"Invalid Slack OAuth response: {token_response}")
            raise LinkedAccountOAuth2Error("Invalid Slack OAuth response")

        return OAuth2SchemeCredentials(
            access_token=authed_user["access_token"],
            token_type=authed_user.get("token_type"),
            refresh_token=authed_user.get("refresh_token"),
            expires_at=int(time.time()) + authed_user.get("expires_in")
            if authed_user.get("expires_in")
            else None,
            raw_token_response=token_response,
        )

    if "access_token" not in token_response:
        logger.error(f"Missing access token in OAuth response: {token_response}")
        raise LinkedAccountOAuth2Error("Missing access token in OAuth response")

    return OAuth2SchemeCredentials(
        access_token=token_response["access_token"],
        token_type=token_response.get("token_type"),
        expires_at=int(time.time()) + token_response["expires_in"]
        if "expires_in" in token_response
        else None,
        refresh_token=token_response.get("refresh_token"),
        raw_token_response=token_response,
    )


def rewrite_oauth2_authorization_url(app_name: str, authorization_url: str) -> str:
    """
    Rewrite OAuth2 authorization URL for specific apps that need special handling.
    Currently handles Slack's special case where user scopes and scopes need to be replaced.
    TODO: this approach is hacky and need to refactor this in the future

    Args:
        app_name: Name of the OAuth2 app (e.g., 'slack')
        authorization_url: The original authorization URL

    Returns:
        The rewritten authorization URL if needed, otherwise the original URL
    """
    if app_name == "SLACK":
        # Slack requires user scopes to be prefixed with 'user_'
        # Replace 'scope=' with 'user_scope=' and add 'scope=' with the null value
        if "scope=" in authorization_url:
            # Extract the original scope value
            scope_start = authorization_url.find("scope=") + 6
            scope_end = authorization_url.find("&", scope_start)
            if scope_end == -1:
                scope_end = len(authorization_url)
            original_scope = authorization_url[scope_start:scope_end]

            # Replace the original scope with user_scope and add scope
            new_url = authorization_url.replace(
                f"scope={original_scope}", f"user_scope={original_scope}&scope="
            )
            return new_url

    return authorization_url
