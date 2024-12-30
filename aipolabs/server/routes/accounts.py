import secrets
from datetime import datetime, timezone
from typing import Annotated, cast
from uuid import UUID

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.accounts import (
    AccountCreate,
    AccountCreateOAuth2State,
    LinkedAccountPublic,
    ListLinkedAccountsFilters,
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
        # create and encode the state payload
        # note: the state payload is jwt encoded (signed), but it's not encrypted, anyone can decode it
        state = AccountCreateOAuth2State(
            integration_id=account_create.integration_id,
            project_id=db_project.id,
            app_id=db_app.id,
            account_name=account_create.account_name,
            iat=int(datetime.now(timezone.utc).timestamp()),
            nonce=secrets.token_urlsafe(16),
        )
        path = request.url_for(ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME).path
        redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
        state_jwt = jwt.encode(
            {"alg": config.JWT_ALGORITHM}, state.model_dump(mode="json"), config.JWT_SECRET_KEY
        ).decode()
        # TODO: add expiration check to the state payload for extra security
        # TODO: how to handle redirect in cli (e.g., parse the redirect url)?
        oauth2_client = _create_oauth2_client(db_app)
        redirect_response = await oauth2_client.authorize_redirect(
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
async def accounts_oauth2_callback(
    request: Request,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> None:
    """
    Callback route for OAuth2 account linking.
    A linked account (with necessary credentials from the OAuth2 provider) will be created in the database.
    """
    state_jwt = request.query_params.get("state")
    logger.info(f"Callback received, state_jwt={state_jwt}")

    if not state_jwt:
        logger.error("Missing state parameter")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state parameter"
        )
    # decode the state payload
    try:
        state = AccountCreateOAuth2State.model_validate(
            jwt.decode(state_jwt, config.JWT_SECRET_KEY)
        )
        logger.info(f"state: {state}")
    except Exception as e:
        logger.error(f"Failed to decode state_jwt={state_jwt}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to decode state"
        )
    # create oauth2 client
    db_app = crud.get_app_by_id(db_session, state.app_id)
    oauth2_client = _create_oauth2_client(db_app)
    # get oauth2 account credentials
    # TODO: can each OAuth2 provider return different fields? if so, need to handle them accordingly. Maybe can
    # store the auth reponse schema in the App record in db. and cast the auth_response to the schema here.
    try:
        logger.info("Retrieving oauth2 token")
        token_response = await oauth2_client.authorize_access_token(request)
        # TODO: remove PII log
        logger.warning(f"oauth2 token requested successfully, token_response: {token_response}")
    except Exception as e:
        logger.error("Failed to retrieve oauth2 token", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to retrieve oauth2 token: {str(e)}")

    # TODO: some of them might be optional (e.g., refresh_token, scope, expires_in, refresh_token_expires_in) and not be provided by the OAuth2 provider
    # we should handle None or provide default values
    security_credentials = {
        "access_token": token_response["access_token"],
        "token_type": token_response["token_type"],
        "expires_in": token_response["expires_in"],
        "scope": token_response["scope"],
        "refresh_token": token_response["refresh_token"],
    }

    try:
        # if the linked account already exists, update it, otherwise create a new one
        db_linked_account = crud.get_linked_account(
            db_session,
            state.project_id,
            state.app_id,
            state.account_name,
        )
        if db_linked_account:
            logger.info(
                f"Updating oauth2 credentials for linked account linked_account_id={db_linked_account.id}"
            )
            db_linked_account.security_scheme = SecurityScheme.OAUTH2
            db_linked_account.security_credentials = security_credentials
        else:
            logger.info(
                f"Creating oauth2 linked account for integration_id={state.integration_id}, "
                f"account_name={state.account_name}"
            )
            db_linked_account = crud.create_linked_account(
                db_session,
                integration_id=state.integration_id,
                project_id=state.project_id,
                app_id=state.app_id,
                account_name=state.account_name,
                security_scheme=SecurityScheme.OAUTH2,
                security_credentials=security_credentials,
                enabled=True,
            )
        db_session.commit()
    except Exception as e:
        logger.error("Failed to create linked account", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create linked account: {str(e)}",
        )


@router.get("/", response_model=list[LinkedAccountPublic])
async def list_linked_accounts(
    filters: Annotated[ListLinkedAccountsFilters, Query()],
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> list[sql_models.LinkedAccount]:
    """
    List all linked accounts under the project (identified by api key), with optional filters.
    As of now, project_id + app_id/app_name + account_name uniquely identify a linked account.
    This can be an alternatively way to GET /accounts/{account_id} for getting a specific linked account.
    """
    logger.info(f"Listing linked accounts for api_key_id={api_key_id}, filters={filters}")

    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    linked_accounts = crud.get_linked_accounts(db_session, db_project.id, filters)
    return linked_accounts


def _create_oauth2_client(db_app: sql_models.App) -> StarletteOAuth2App:
    """
    Create an OAuth2 client for the given app.
    """
    # TODO: create our own oauth2 client to abstract away the details and the authlib dependency, and
    # it would be easier if later we decide to implement oauth2 requests manually.
    # TODO: add correspinding validation of the oauth2 fields (e.g., client_id, client_secret, scope, etc.) when indexing an App.
    # TODO: load client's overrides if they specify any, for example, client_id, client_secret, scope, etc.

    # security_scheme of the integration must be one of the App's security_schemes, so we can safely cast it
    app_default_oauth2_config = cast(dict, db_app.security_schemes[SecurityScheme.OAUTH2])
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
    return cast(StarletteOAuth2App, oauth_client)


@router.get("/{account_id}", response_model=LinkedAccountPublic)
async def get_linked_account(
    account_id: UUID,
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> sql_models.LinkedAccount:
    """
    Get a linked account by its id.
    """
    # validations
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    db_linked_account = crud.get_linked_account_by_id(db_session, account_id)
    if not db_linked_account:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "account not found")
    if db_linked_account.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The linked account does not belong to the project",
        )
    return db_linked_account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_linked_account(
    account_id: UUID,
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> None:
    """
    Delete a linked account by its id.
    """
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    db_linked_account = crud.get_linked_account_by_id(db_session, account_id)
    if not db_linked_account:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "account not found")
    if db_linked_account.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The linked account does not belong to the project",
        )
    crud.delete_linked_account(db_session, account_id)
    db_session.commit()

    return None


# TODO: add a route to update a linked account
