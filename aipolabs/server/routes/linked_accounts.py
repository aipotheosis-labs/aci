import secrets
from datetime import datetime, timezone
from typing import Annotated, cast
from uuid import UUID

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.exceptions import (
    AppConfigurationNotFound,
    AppNotFound,
    AuthenticationError,
    LinkedAccountNotFound,
    NoImplementationFound,
    UnexpectedException,
)
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.linked_accounts import (
    LinkedAccountCreate,
    LinkedAccountCreateOAuth2State,
    LinkedAccountPublic,
    LinkedAccountsList,
)
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
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    body: LinkedAccountCreate,
) -> RedirectResponse:
    """
    Start an account linking process.
    The app configuration for the app determines the security scheme to use for the account linking process.
    - If security_scheme configured in the app configuration is OAUTH2, this will return a redirect url to the OAuth2
      provider's authorization endpoint, and a linked account will be created in the database after the end user
      grants permission.
    - If security_scheme configured in the app configuration is API_KEY, the api_key field in the request body is required.
    """
    logger.info(
        f"Linking account for api_key_id={context.api_key_id}, "
        f"app_id={body.app_id}, "
        f"linked_account_owner_id={body.linked_account_owner_id}"
    )
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, body.app_id
    )
    if not app_configuration:
        logger.error(
            f"configuration for app={body.app_id} not found for project={context.project.id}"
        )
        raise AppConfigurationNotFound(
            f"configuration for app={body.app_id} not found for project={context.project.id}"
        )

    # for OAuth2 account, we need to redirect to the OAuth2 provider's authorization endpoint
    if app_configuration.security_scheme == SecurityScheme.OAUTH2:
        # create and encode the state payload
        # note: the state payload is jwt encoded (signed), but it's not encrypted, anyone can decode it
        state = LinkedAccountCreateOAuth2State(
            app_id=body.app_id,
            project_id=context.project.id,
            linked_account_owner_id=body.linked_account_owner_id,
            iat=int(datetime.now(timezone.utc).timestamp()),
            nonce=secrets.token_urlsafe(16),
        )
        path = request.url_for(ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME).path
        redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
        state_jwt = jwt.encode(
            {"alg": config.JWT_ALGORITHM}, state.model_dump(mode="json"), config.JWT_SECRET_KEY
        ).decode()
        # TODO: add expiration check to the state payload for extra security
        # TODO: how to handle redirect in cli (e.g., parse the redirect url)? return JSONResponse(content={"redirect_url": redirect_url})
        # instead of RedirectResponse
        oauth2_client = _create_oauth2_client(app_configuration.app)
        redirect_response = await oauth2_client.authorize_redirect(
            request, redirect_uri, state=state_jwt
        )

        return redirect_response

    elif app_configuration.security_scheme == SecurityScheme.API_KEY:
        # TODO: ... handle API key ...
        raise NoImplementationFound("API key security scheme is not implemented yet")

    else:
        # Should never reach here as all security schemes stored in the db should be supported
        logger.error(
            f"unsupported security scheme={app_configuration.security_scheme} "
            f"for app={body.app_id}"
        )
        raise UnexpectedException(
            f"unsupported security scheme={app_configuration.security_scheme} "
            f"for app={body.app_id}"
        )


@router.get("/oauth2/callback", name=ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME)
async def linked_accounts_oauth2_callback(
    request: Request,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> None:
    """
    Callback endpoint for OAuth2 account linking.
    - A linked account (with necessary credentials from the OAuth2 provider) will be created in the database.
    """
    state_jwt = request.query_params.get("state")
    logger.info(f"Callback received, state_jwt={state_jwt}")

    if not state_jwt:
        logger.error("Missing state parameter")
        raise AuthenticationError("Missing state parameter")
    # decode the state payload
    try:
        state = LinkedAccountCreateOAuth2State.model_validate(
            jwt.decode(state_jwt, config.JWT_SECRET_KEY)
        )
        logger.info(f"state: {state}")
    except Exception:
        logger.exception(f"failed to decode state_jwt={state_jwt}")
        raise AuthenticationError("failed to decode state")

    # create oauth2 client
    app = crud.apps.get_app(db_session, state.app_id, False, True)
    if not app:
        logger.error(f"app={state.app_id} not found")
        raise AppNotFound(state.app_id)

    oauth2_client = _create_oauth2_client(app)
    # get oauth2 account credentials
    # TODO: can each OAuth2 provider return different fields? if so, need to handle them accordingly. Maybe can
    # store the auth reponse schema in the App record in db. and cast the auth_response to the schema here.
    try:
        logger.info("retrieving oauth2 token")
        token_response = await oauth2_client.authorize_access_token(request)
        # TODO: remove PII log
        logger.warning(f"oauth2 token requested successfully, token_response: {token_response}")
    except Exception:
        logger.exception("failed to retrieve oauth2 token")
        raise AuthenticationError("failed to retrieve oauth2 token")

    # TODO: some of them might be optional (e.g., refresh_token, scope, expires_in, refresh_token_expires_in) and not provided by the OAuth2 provider
    # we should handle None or provide default values (using pydantic)
    security_credentials = {
        "access_token": token_response["access_token"],
        "token_type": token_response["token_type"],
        "expires_in": token_response["expires_in"],
        "scope": token_response["scope"],
        "refresh_token": token_response["refresh_token"],
    }

    # if the linked account already exists, update it, otherwise create a new one
    # TODO: consider separating the logic for updating and creating a linked account or give warning to clients
    # if the linked account already exists to avoid accidental overwriting the account
    # TODO: try/except, retry?
    linked_account = crud.linked_accounts.get_linked_account(
        db_session,
        state.project_id,
        state.app_id,
        state.linked_account_owner_id,
    )
    if linked_account:
        logger.info(
            f"Updating oauth2 credentials for linked account linked_account_id={linked_account.id}"
        )
        linked_account = crud.linked_accounts.update_linked_account(
            db_session, linked_account, SecurityScheme.OAUTH2, security_credentials
        )
    else:
        logger.info(
            f"Creating oauth2 linked account for project_id={state.project_id}, "
            f"app_id={state.app_id}, linked_account_owner_id={state.linked_account_owner_id}"
        )
        linked_account = crud.linked_accounts.create_linked_account(
            db_session,
            project_id=state.project_id,
            app_id=state.app_id,
            linked_account_owner_id=state.linked_account_owner_id,
            security_scheme=SecurityScheme.OAUTH2,
            security_credentials=security_credentials,
            enabled=True,
        )
    db_session.commit()


# TODO: add pagination
@router.get("/", response_model=list[LinkedAccountPublic])
async def list_linked_accounts(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[LinkedAccountsList, Query()],
) -> list[LinkedAccount]:
    """
    List all linked accounts.
    - Optionally filter by app_id and linked_account_owner_id.
    - app_id + linked_account_owner_id can uniquely identify a linked account.
    - This can be an alternatively way to GET /linked-accounts/{linked_account_id} for getting a specific linked account.
    """
    logger.info(
        f"Listing linked accounts for api_key_id={context.api_key_id}, query_params={query_params}"
    )

    linked_accounts = crud.linked_accounts.get_linked_accounts(
        context.db_session,
        context.project.id,
        query_params.app_id,
        query_params.linked_account_owner_id,
    )
    return linked_accounts


def _create_oauth2_client(app: App) -> StarletteOAuth2App:
    """
    Create an OAuth2 client for the given app.
    """
    # TODO: create our own oauth2 client to abstract away the details and the authlib dependency, and
    # it would be easier if later we decide to implement oauth2 requests manually.
    # TODO: add correspinding validation of the oauth2 fields (e.g., client_id, client_secret, scope, etc.) when indexing an App.
    # TODO: load client's overrides if they specify any, for example, client_id, client_secret, scope, etc.

    # security_scheme of the app configuration must be one of the App's security_schemes, so we can safely cast it
    app_default_oauth2_config = cast(dict, app.security_schemes[SecurityScheme.OAUTH2])
    oauth_client = OAuth().register(
        name=app.name,
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
    return cast(StarletteOAuth2App, oauth_client)


@router.get("/{linked_account_id}", response_model=LinkedAccountPublic)
async def get_linked_account(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    linked_account_id: UUID,
) -> LinkedAccount:
    """
    Get a linked account by its id.
    - linked_account_id uniquely identifies a linked account across the platform.
    """
    # validations
    linked_account = crud.linked_accounts.get_linked_account_by_id(
        context.db_session, linked_account_id, context.project.id
    )
    if not linked_account:
        logger.error(f"linked account={linked_account_id} not found")
        raise LinkedAccountNotFound(str(linked_account_id))

    return linked_account


@router.delete("/{linked_account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_linked_account(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    linked_account_id: UUID,
) -> None:
    """
    Delete a linked account by its id.
    """
    linked_account = crud.linked_accounts.get_linked_account_by_id(
        context.db_session, linked_account_id, context.project.id
    )
    if not linked_account:
        logger.error(f"linked account={linked_account_id} not found")
        raise LinkedAccountNotFound(str(linked_account_id))

    crud.linked_accounts.delete_linked_account(context.db_session, linked_account)

    context.db_session.commit()


# TODO: add a route to update a linked account (e.g., enable/disable, change account name, etc.)
