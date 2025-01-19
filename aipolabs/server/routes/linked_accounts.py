import json
from typing import Annotated, Any, cast
from uuid import UUID

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.exceptions import (
    AppConfigurationNotFound,
    AppNotFound,
    AuthenticationError,
    LinkedAccountNotFound,
    LinkedAccountOAuth2Error,
    NoImplementationFound,
)
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.linked_accounts import (
    LinkedAccountOAuth2Create,
    LinkedAccountOAuth2CreateState,
    LinkedAccountPublic,
    LinkedAccountsList,
)
from aipolabs.common.schemas.security_scheme import OAuth2Scheme
from aipolabs.server import config
from aipolabs.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)

LINKED_ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME = "linked_accounts_oauth2_callback"

"""
IMPORTANT NOTE:
The api endpoints (both URL design and implementation) for linked accounts are currently a bit hacky, especially for OAuth2 account type.
Will revisit and potentially refactor later once we have more time and more clarity on the requirements.
There are a few tricky parts:
- There are different types of linked accounts (OAuth2, API key, etc.) And the OAuth2 type linking flow
  is very different from the other types.
- For OAuth2 account linking, we want to support quite a few scenarios that might require different
  flows or setups. But for simplicity, we currently hack together an implementation that works for all,
  with some compromises on the security. (well, I'd say it's still secure enough for this stage but need to
  revisit and improve later.). These OAuth2 scenarios include:
  - Scenario 1: allow (our direct) client to link an OAuth2 account on developer portal.
  - Scenario 2: allow (client's) end user to link an OAuth2 account with the redirect url.
    - Scenario 2.1: Client generates the redirect url and sends it to the end user.
    - Scenario 2.2: Amid end user's conversation with the client's AI agent, the AI agent generates the
      redirect url for OAuth2 account linking. (If the App the end user needs access too is not yet authenticated)
  - Scenario 3: allow (our direct) client to generate a link to a webpage that we host for OAuth2 account linking.
    Different from Scenario 2.1, the link is not a redirect url but a link to a webpage that we host. And potentially
    can work for other types of accounting linking, e.g., allowend user to input API key.

- Also see: https://www.notion.so/Replace-authlib-to-support-both-browser-and-cli-authentication-16f8378d6a4780eda593ef149a205198
"""


# TODO:
# Note:
# - For token refresh (when executing functions), either use authlib's oauth2 client/session or build the request manually.
#   If doing mannually, might need to handle dynamic url dicovery via discovery doc (e.g., google)
@router.get("/oauth2")
async def link_oauth2_account(
    request: Request,
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[LinkedAccountOAuth2Create, Query()],
) -> dict:
    """
    Start an OAuth2 account linking process.
    It will return a redirect url (as a string, instead of RedirectResponse) to the OAuth2 provider's authorization endpoint.
    """
    logger.info(
        f"Linking OAuth2 account for project={context.project.id}, "
        f"app={query_params.app_id}, "
        f"linked_account_owner_id={query_params.linked_account_owner_id}"
    )
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, query_params.app_id
    )
    if not app_configuration:
        logger.error(
            f"configuration for app={query_params.app_id} not found for project={context.project.id}"
        )
        raise AppConfigurationNotFound(
            f"configuration for app={query_params.app_id} not found for project={context.project.id}"
        )
    # TODO: for now we require the security_schema used for accounts under an App must be the same as the security_schema configured in the app
    # configuration. But in the future, we might lift this restriction and allow any security_schema as long the App supports it.
    if app_configuration.security_scheme != SecurityScheme.OAUTH2:
        logger.error(
            f"app={query_params.app_id} is not configured with OAuth2, but {app_configuration.security_scheme}"
        )
        raise NoImplementationFound(
            f"app={query_params.app_id} is not configured with OAuth2, but {app_configuration.security_scheme}"
        )

    oauth2_client = _create_oauth2_client(app_configuration.app)
    path = request.url_for(LINKED_ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
    # NOTE: normally we should generate "state"/"state_jwt" first, and then
    # call authorize_redirect(request, redirect_uri, state=state_jwt), within which calls create_authorization_url() and save_authorize_data().
    # But as we mentioned at the beginning of this file, we need to be a bit hacky to avoid any browser session related implementation.
    # Here we just call create_authorization_url() to get the generated authorization_data, and we genrate a new 'state'
    # value that contains both data from the authorization_data and data we need for further processing (like app_id,
    # project_id, linked_account_owner_id, etc.), and replace the 'state' value in the url parameter with the new 'state' (jwt) value.
    # In the callback endpoint, we will also need to manually parse the 'state' data and reconstruct the 'url' before calling fetch_access_token(), instead of calling
    # authorize_access_token() directly in a normal oauth2 flow.

    # authorization_data exmaple:
    # {
    #     "code_verifier": "...",
    #     "state": "...",
    #     "url": "https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=...&scope=...&response_type=code&access_type=offline&state=...&code_verifier=...&nonce=...",
    #     "nonce": "..."
    # }

    # the saved data (by calling save_authorize_data(request, redirect_uri=redirect_uri, **authorization_data), which also
    # sets the request.session) is a bit different from the authrization data:
    # {
    # "_state_GOOGLE_CALENDAR_keyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsImV4cCI6MTUxNjI0MjYyMiwiaXNzIjoibXlfaXNzdWVyIiwic3ViIjoibXlfc3ViamVjdCIsImF1ZCI6Im15X2F1ZGllbmNlIiwibmJmIjoxNTE2MjM5MDIyfQ.lgk5D-k4-tMsMKnTJd02v2tczPbQ9M87qOTtX-lCbX8": {
    #     "data": {
    #         "redirect_uri": "http://localhost:8000/v1/accounts/oauth2/callback",
    #         "code_verifier": "NjpsQtcuLUNPAM5NQuMhE2UUavVB0BtYo0Ggr6EO3HPpGkxm",
    #         "nonce": "Lr0KlHBM4ttofP16q9Hv",
    #         "url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=621325784080-uuu3mt1vvfmffbvdb7gj6ijq08q2iopi.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fv1%2Faccounts%2Foauth2%2Fcallback&scope=openid+email+profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&state=eyJpYXQiOjE1MTYyMzkwMjIsImV4cCI6MTUxNjI0MjYyMiwiaXNzIjoibXlfaXNzdWVyIiwic3ViIjoibXlfc3ViamVjdCIsImF1ZCI6Im15X2F1ZGllbmNlIiwibmJmIjoxNTE2MjM5MDIyfQ.lgk5D-k4-tMsMKnTJd02v2tczPbQ9M87qOTtX-lCbX8&access_type=offline&nonce=Lr0KlHBM4ttofP16q9Hv&prompt=consent"
    #     },
    #     "exp": 1735786775.4127536
    # }
    authorization_data = await oauth2_client.create_authorization_url(redirect_uri)
    logger.info(f"authorization_data: \n {json.dumps(authorization_data, indent=2)}")
    # create and encode the state payload. Including code_verifier in state is definitely a compromise.
    # NOTE: the state payload is jwt encoded (signed), but it's not encrypted, anyone can decode it
    # TODO: add expiration check to the state payload for extra security
    new_state = LinkedAccountOAuth2CreateState(
        app_id=query_params.app_id,
        project_id=context.project.id,
        linked_account_owner_id=query_params.linked_account_owner_id,
        redirect_uri=redirect_uri,
        code_verifier=authorization_data["code_verifier"],
        nonce=authorization_data.get("nonce", None),  # nonce only exists for openid
    )
    new_state_jwt = jwt.encode(
        {"alg": config.JWT_ALGORITHM}, new_state.model_dump(mode="json"), config.SIGNING_KEY
    ).decode()  # decode() is needed to convert the bytes to a string (not decoding the jwt payload) for this jwt library.

    # replace the state jwt token in the url parameter with the new state_jwt
    return {
        "url": str(authorization_data["url"]).replace(authorization_data["state"], new_state_jwt)
    }


@router.get(
    "/oauth2/callback",
    name=LINKED_ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME,
    response_model=LinkedAccountPublic,
)
async def linked_accounts_oauth2_callback(
    request: Request,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> LinkedAccount:
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
        state = LinkedAccountOAuth2CreateState.model_validate(
            jwt.decode(state_jwt, config.SIGNING_KEY)
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
        token_response = await _authorize_access_token(
            oauth2_client, request, state.redirect_uri, state.code_verifier, state.nonce
        )
        # TODO: remove PII log
        logger.warning(f"oauth2 token requested successfully, token_response: {token_response}")
    except Exception:
        logger.exception("failed to retrieve oauth2 token")
        raise AuthenticationError("failed to retrieve oauth2 token")

    # TODO: some of them might be optional (e.g., refresh_token, scope, expires_in, refresh_token_expires_in) and not provided by the OAuth2 provider
    # we should handle None or provide default values (using pydantic)
    # TODO: we might want to verify scope authorized by end user is what we required
    security_credentials = {
        "access_token": token_response["access_token"],
        "token_type": token_response["token_type"],
        "expires_in": token_response["expires_in"],
        "scope": token_response["scope"],
        "refresh_token": token_response["refresh_token"],
    }
    logger.info(f"security_credentials: \n {json.dumps(security_credentials, indent=2)}")

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
        logger.info(f"updating oauth2 credentials for linked account={linked_account.id}")
        linked_account = crud.linked_accounts.update_linked_account(
            db_session, linked_account, SecurityScheme.OAUTH2, security_credentials
        )
    else:
        logger.info(
            f"creating oauth2 linked account for project={state.project_id}, "
            f"app={state.app_id}, linked_account_owner_id={state.linked_account_owner_id}"
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

    return linked_account


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
    app_default_oauth2_config = cast(OAuth2Scheme, app.security_schemes[SecurityScheme.OAUTH2])
    oauth_client = OAuth().register(
        name=app.name,
        client_id=app_default_oauth2_config.client_id,
        client_secret=app_default_oauth2_config.client_secret,
        client_kwargs={
            "scope": app_default_oauth2_config.scope,
            "prompt": "consent",
            "code_challenge_method": "S256",
        },
        # Note: usually if server_metadata_url (e.g., google's discovery doc https://accounts.google.com/.well-known/openid-configuration)
        # is provided, the other endpoints are not needed.
        authorize_url=app_default_oauth2_config.authorize_url,
        authorize_params={"access_type": "offline"},
        access_token_url=app_default_oauth2_config.access_token_url,
        refresh_token_url=app_default_oauth2_config.refresh_token_url,
        server_metadata_url=app_default_oauth2_config.server_metadata_url,
    )
    return cast(StarletteOAuth2App, oauth_client)


# a modified version of the authorize_access_token method in authlib/integrations/starlette_client/apps.py
async def _authorize_access_token(
    oauth2_client: StarletteOAuth2App,
    request: Request,
    redirect_uri: str,
    code_verifier: str,
    nonce: str | None = None,
    **kwargs: Any,
) -> dict:
    error = request.query_params.get("error")
    if error:
        description = request.query_params.get("error_description")
        logger.error(f"OAuth2 error: {error}, error_description: {description}")
        raise LinkedAccountOAuth2Error(message=description)

    params = {
        "code": request.query_params.get("code"),
        "state": request.query_params.get("state"),
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    claims_options = kwargs.pop("claims_options", None)
    token = cast(dict, await oauth2_client.fetch_access_token(**params, **kwargs))

    if "id_token" in token and nonce:
        userinfo = await oauth2_client.parse_id_token(
            token, nonce=nonce, claims_options=claims_options
        )
        token["userinfo"] = userinfo
    return token


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
