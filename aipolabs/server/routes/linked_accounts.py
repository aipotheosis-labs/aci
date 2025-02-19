import json
import time
from typing import Annotated
from uuid import UUID

from authlib.jose import jwt
from fastapi import APIRouter, Body, Depends, Query, Request, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.exceptions import (
    AppConfigurationNotFound,
    AppNotFound,
    AuthenticationError,
    LinkedAccountNotFound,
    NoImplementationFound,
)
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.linked_accounts import (
    LinkedAccountDefaultCreate,
    LinkedAccountOAuth2Create,
    LinkedAccountOAuth2CreateState,
    LinkedAccountPublic,
    LinkedAccountsList,
)
from aipolabs.common.schemas.security_scheme import (
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aipolabs.server import config
from aipolabs.server import dependencies as deps
from aipolabs.server import oauth2

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


@router.post("/default", response_model=LinkedAccountPublic)
async def link_account_with_aipolabs_default_credentials(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    body: Annotated[LinkedAccountDefaultCreate, Body()],
) -> LinkedAccount:
    """
    Create a linked account under an App using default credentials (e.g., API key, OAuth2, etc.)
    provided by Aipolabs.
    If there is no default credentials provided by Aipolabs for the specific App, the linked account will not be created,
    and an error will be returned.
    """
    logger.info(
        f"Linking account with Aipolabs default credentials for project={context.project.id}, "
        f"app={body.app_name}, linked_account_owner_id={body.linked_account_owner_id}"
    )
    # TODO: some duplicate code with other linked account creation routes
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, body.app_name
    )
    if not app_configuration:
        logger.error(
            f"configuration for app={body.app_name} not found for project={context.project.id}"
        )
        raise AppConfigurationNotFound(
            f"configuration for app={body.app_name} not found for project={context.project.id}"
        )

    # need to make sure the App actully has default credentials provided by Aipolabs
    app_default_credentials = app_configuration.app.default_security_credentials_by_scheme.get(
        app_configuration.security_scheme
    )
    if not app_default_credentials:
        logger.error(
            f"no default credentials provided by Aipolabs for app={body.app_name}, "
            f"security_scheme={app_configuration.security_scheme}"
        )
        # TODO: consider choosing a different exception type?
        raise NoImplementationFound(
            f"no default credentials provided by Aipolabs for app={body.app_name}, "
            f"security_scheme={app_configuration.security_scheme}"
        )

    linked_account = crud.linked_accounts.get_linked_account(
        context.db_session,
        context.project.id,
        body.app_name,
        body.linked_account_owner_id,
    )
    # TODO: same as OAuth2 linked account creation, we might want to separate the logic for updating and creating a linked account
    # or give warning to clients if the linked account already exists to avoid accidental overwriting the account
    if linked_account:
        logger.info(f"updating linked_account={linked_account.id} with default credentials")
        linked_account = crud.linked_accounts.update_linked_account(
            context.db_session, linked_account, app_configuration.security_scheme, {}
        )
    else:
        logger.info(
            f"creating linked account with default credentials for project={context.project.id}, "
            f"app={body.app_name}, linked_account_owner_id={body.linked_account_owner_id}"
        )
        linked_account = crud.linked_accounts.create_linked_account(
            context.db_session,
            context.project.id,
            body.app_name,
            body.linked_account_owner_id,
            app_configuration.security_scheme,
            enabled=True,
        )
    context.db_session.commit()

    return linked_account


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
        f"app={query_params.app_name}, "
        f"linked_account_owner_id={query_params.linked_account_owner_id}"
    )
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, query_params.app_name
    )
    if not app_configuration:
        logger.error(
            f"configuration for app={query_params.app_name} not found for project={context.project.id}"
        )
        raise AppConfigurationNotFound(
            f"configuration for app={query_params.app_name} not found for project={context.project.id}"
        )
    # TODO: for now we require the security_schema used for accounts under an App must be the same as the security_schema configured in the app
    # configuration. But in the future, we might lift this restriction and allow any security_schema as long the App supports it.
    if app_configuration.security_scheme != SecurityScheme.OAUTH2:
        error_message = (
            f"the security_scheme configured in app={query_params.app_name} is "
            f"{app_configuration.security_scheme} not OAuth2"
        )
        logger.error(error_message)
        raise NoImplementationFound(error_message)

    # TODO: add correspinding validation of the oauth2 fields (e.g., client_id, client_secret, scope, etc.)
    # when indexing an App. For example, if server_metadata_url is None, other url must be provided
    # TODO: load client's overrides if they specify any, for example, client_id, client_secret, scope, etc.
    # security_scheme of the app configuration must be one of the App's security_schemes, so we can safely validate it
    app_default_oauth2_config = OAuth2Scheme.model_validate(
        app_configuration.app.security_schemes[SecurityScheme.OAUTH2]
    )
    oauth2_client = oauth2.create_oauth2_client(
        name=app_configuration.app.name,
        client_id=app_default_oauth2_config.client_id,
        client_secret=app_default_oauth2_config.client_secret,
        scope=app_default_oauth2_config.scope,
        token_endpoint_auth_method=app_default_oauth2_config.token_endpoint_auth_method,
        authorize_url=app_default_oauth2_config.authorize_url,
        access_token_url=app_default_oauth2_config.access_token_url,
        refresh_token_url=app_default_oauth2_config.refresh_token_url,
        server_metadata_url=app_default_oauth2_config.server_metadata_url,
    )
    path = request.url_for(LINKED_ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
    # NOTE: normally we should generate "state"/"state_jwt" first, and then
    # call authorize_redirect(request, redirect_uri, state=state_jwt), within which calls create_authorization_url() and save_authorize_data().
    # But as we mentioned at the beginning of this file, we need to be a bit hacky to avoid any browser session related implementation.
    # Here we just call create_authorization_url() to get the generated authorization_data, and we genrate a new 'state'
    # value that contains both data from the authorization_data and data we need for further processing (like app_name,
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
    authorization_data = await oauth2.create_authorization_url(oauth2_client, redirect_uri)
    logger.info(f"authorization_data: \n {json.dumps(authorization_data, indent=2)}")
    # create and encode the state payload. Including code_verifier in state is definitely a compromise.
    # NOTE: the state payload is jwt encoded (signed), but it's not encrypted, anyone can decode it
    # TODO: add expiration check to the state payload for extra security
    new_state = LinkedAccountOAuth2CreateState(
        app_name=query_params.app_name,
        project_id=context.project.id,
        linked_account_owner_id=query_params.linked_account_owner_id,
        redirect_uri=redirect_uri,
        code_verifier=authorization_data["code_verifier"],
        nonce=authorization_data.get("nonce", None),  # nonce only exists for openid
        after_oauth2_link_redirect_url=query_params.after_oauth2_link_redirect_url,
    )
    new_state_jwt = jwt.encode(
        {"alg": config.JWT_ALGORITHM},
        new_state.model_dump(mode="json", exclude_none=True),
        config.SIGNING_KEY,
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
) -> LinkedAccount | RedirectResponse:
    """
    Callback endpoint for OAuth2 account linking.
    - A linked account (with necessary credentials from the OAuth2 provider) will be created in the database.
    """
    state_jwt = request.query_params.get("state")
    logger.info(f"Callback received, state_jwt={state_jwt}")

    if not state_jwt:
        logger.error("Missing state parameter in account linking callback")
        raise AuthenticationError("missing state parameter during account linking")
    # decode the state payload
    try:
        state = LinkedAccountOAuth2CreateState.model_validate(
            jwt.decode(state_jwt, config.SIGNING_KEY)
        )
        logger.info(f"state: {state}")
    except Exception:
        logger.exception(f"failed to decode state_jwt={state_jwt}")
        raise AuthenticationError("invalid state parameter during account linking")

    # create oauth2 client
    app = crud.apps.get_app(db_session, state.app_name, False, True)
    if not app:
        logger.error(f"app={state.app_name} not found")
        raise AppNotFound(f"app={state.app_name} not found")

    app_default_oauth2_config = OAuth2Scheme.model_validate(
        app.security_schemes[SecurityScheme.OAUTH2]
    )
    oauth2_client = oauth2.create_oauth2_client(
        name=app.name,
        client_id=app_default_oauth2_config.client_id,
        client_secret=app_default_oauth2_config.client_secret,
        scope=app_default_oauth2_config.scope,
        token_endpoint_auth_method=app_default_oauth2_config.token_endpoint_auth_method,
        authorize_url=app_default_oauth2_config.authorize_url,
        access_token_url=app_default_oauth2_config.access_token_url,
        refresh_token_url=app_default_oauth2_config.refresh_token_url,
        server_metadata_url=app_default_oauth2_config.server_metadata_url,
    )

    # get oauth2 account credentials
    # TODO: can each OAuth2 provider return different fields? if so, need to handle them accordingly. Maybe can
    # store the auth reponse schema in the App record in db. and cast the auth_response to the schema here.
    try:
        logger.info("retrieving oauth2 token")
        token_response = await oauth2.authorize_access_token_without_browser_session(
            oauth2_client, request, state.redirect_uri, state.code_verifier, state.nonce
        )
        # TODO: remove PII log
        logger.warning(f"oauth2 token requested successfully, token_response: {token_response}")
    except Exception:
        logger.exception("failed to retrieve oauth2 token")
        raise AuthenticationError("failed to retrieve oauth2 token during account linking")

    # TODO: we might want to verify scope authorized by end user (token_response["scope"]) is what we asked
    security_credentials = OAuth2SchemeCredentials(
        access_token=token_response["access_token"],
        token_type=token_response.get("token_type", None),
        expires_at=(
            int(time.time()) + token_response["expires_in"]
            if "expires_in" in token_response
            else None
        ),
        refresh_token=token_response.get("refresh_token", None),
    )
    logger.info(
        f"security_credentials: \n {json.dumps(security_credentials.model_dump(mode='json'), indent=2)}"
    )

    # if the linked account already exists, update it, otherwise create a new one
    # TODO: consider separating the logic for updating and creating a linked account or give warning to clients
    # if the linked account already exists to avoid accidental overwriting the account
    # TODO: try/except, retry?
    linked_account = crud.linked_accounts.get_linked_account(
        db_session,
        state.project_id,
        state.app_name,
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
            f"app={state.app_name}, linked_account_owner_id={state.linked_account_owner_id}"
        )
        linked_account = crud.linked_accounts.create_linked_account(
            db_session,
            project_id=state.project_id,
            app_name=state.app_name,
            linked_account_owner_id=state.linked_account_owner_id,
            security_scheme=SecurityScheme.OAUTH2,
            security_credentials=security_credentials,
            enabled=True,
        )
    db_session.commit()

    if state.after_oauth2_link_redirect_url:
        return RedirectResponse(
            url=state.after_oauth2_link_redirect_url, status_code=status.HTTP_302_FOUND
        )

    return linked_account


# TODO: add pagination
@router.get("/", response_model=list[LinkedAccountPublic])
async def list_linked_accounts(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    query_params: Annotated[LinkedAccountsList, Query()],
) -> list[LinkedAccount]:
    """
    List all linked accounts.
    - Optionally filter by app_name and linked_account_owner_id.
    - app_name + linked_account_owner_id can uniquely identify a linked account.
    - This can be an alternatively way to GET /linked-accounts/{linked_account_id} for getting a specific linked account.
    """
    logger.info(
        f"Listing linked accounts for api_key_id={context.api_key_id}, query_params={query_params}"
    )

    linked_accounts = crud.linked_accounts.get_linked_accounts(
        context.db_session,
        context.project.id,
        query_params.app_name,
        query_params.linked_account_owner_id,
    )
    return linked_accounts


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
        raise LinkedAccountNotFound(f"linked account={linked_account_id} not found")

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
        raise LinkedAccountNotFound(f"linked account={linked_account_id} not found")

    crud.linked_accounts.delete_linked_account(context.db_session, linked_account)

    context.db_session.commit()


# TODO: add a route to update a linked account (e.g., enable/disable, change account name, etc.)
