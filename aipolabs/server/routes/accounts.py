import secrets
from datetime import datetime, timezone
from typing import Annotated, cast
from uuid import UUID

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.accounts import AccountCreate
from aipolabs.server import config
from aipolabs.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)

ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME = "accounts_oauth2_callback"


# TODO:
# Note:
# - For token refresh (when executing functions), either use authlib's oauth2 client/session or build the request manually.
#   If doing mannually, might need to handle dynamic url dicovery via discovery doc (e.g., google)
@router.post("/")
async def link_account(
    request: Request,
    account_create: AccountCreate,
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse:
    logger.info(
        f"Linking account for api_key_id={api_key_id}, "
        f"integration_id={account_create.integration_id}, "
        f"account_name={account_create.account_name}"
    )
    # validations
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    db_integration = crud.get_integration(db_session, account_create.integration_id)
    if not db_integration:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
    if db_integration.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The integration does not belong to the project",
        )
    db_app = crud.get_app_by_id(db_session, db_integration.app_id)

    # for OAuth2 account, we need to redirect to the OAuth2 provider's authorization endpoint
    if db_integration.security_scheme == SecurityScheme.OAUTH2:
        # security_scheme of the integration must be one of the App's security_schemes
        app_default_oauth2_config: dict = db_app.security_schemes[SecurityScheme.OAUTH2]
        # TODO: create our own oauth2 client to abstract away the details and the authlib dependency, and
        # it would be easier if later we decide to implement oauth2 requests manually.
        # TODO: add correspinding validation of the oauth2 fields (e.g., client_id, client_secret, scope, etc.) when indexing an App.
        # TODO: load client's overrides if they specify any, for example, client_id, client_secret, scope, etc.
        oauth_client = OAuth().register(
            name=db_app.name,
            client_id=app_default_oauth2_config["client_id"],
            client_secret=app_default_oauth2_config["client_secret"],
            client_kwargs={
                "scope": app_default_oauth2_config["scope"],
                "prompt": "consent",
                "code_challenge_method": "S256",
            },
            # Note: usually if server_metadata_url (e.g., google's discovery doc https://accounts.google.com/.well-known/openid-configuration)
            # is provided, the other endpoints are not needed.
            authorize_url=app_default_oauth2_config.get("authorize_url", None),
            authorize_params={"access_type": "offline"},
            access_token_url=app_default_oauth2_config.get("access_token_url", None),
            refresh_token_url=app_default_oauth2_config.get("refresh_token_url", None),
            server_metadata_url=app_default_oauth2_config.get("server_metadata_url", None),
        )
        oauth_client = cast(StarletteOAuth2App, oauth_client)

        # create and encode the state payload
        # note: the state payload is jwt encoded (signed), but it's not encrypted, anyone can decode it
        state = {
            "integration_id": str(account_create.integration_id),
            "account_name": account_create.account_name,
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "nonce": secrets.token_urlsafe(16),
        }
        path = request.url_for(ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME).path
        redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
        state_jwt = jwt.encode({"alg": config.JWT_ALGORITHM}, state, config.JWT_SECRET_KEY).decode()
        # TODO: add expiration check to the state payload for extra security
        # TODO: how to handle redirect in cli (e.g., parse the redirect url)?
        redirect_response = await oauth_client.authorize_redirect(
            request, redirect_uri, state=state_jwt
        )
        logger.info(
            f"Initiating OAuth2 account linking for integration_id={account_create.integration_id}, "
            f"app={db_app.name}, account={account_create.account_name}, redirect_uri={redirect_uri}"
            f"response_url={redirect_response.headers['location']}"
        )
        return redirect_response

    elif db_integration.security_scheme == SecurityScheme.API_KEY:
        # TODO: ... handle API key ...
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="API key security scheme is not implemented yet",
        )

    else:
        # Should never reach here as all security schemes stored in the db should be supported
        logger.error(
            f"Unexpected error: Unsupported security scheme: {db_integration.security_scheme} for integration_id={account_create.integration_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error: Unsupported security scheme",
        )


@router.get("/oauth2/callback", name=ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME)
async def accounts_oauth2_callback(request: Request) -> None:
    logger.info(f"Callback received for route: {ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME}")
    state_jwt = request.query_params.get("state")
    logger.info(f"state_jwt: {state_jwt}")
    if not state_jwt:
        logger.error("Missing state parameter")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state parameter"
        )
    try:
        state = jwt.decode(state_jwt, config.JWT_SECRET_KEY)
        logger.info(f"state: {state}")
    except Exception as e:
        logger.error(f"Failed to decode state: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to decode state"
        )
    return None
