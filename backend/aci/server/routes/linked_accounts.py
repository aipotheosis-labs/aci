from typing import Annotated
from uuid import UUID

from authlib.jose import jwt
from fastapi import APIRouter, Body, Depends, Query, Request, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from aci.common.db import crud
from aci.common.db.sql_models import LinkedAccount
from aci.common.enums import SecurityScheme
from aci.common.exceptions import (
    AppConfigurationNotFound,
    AppNotFound,
    AuthenticationError,
    LinkedAccountAlreadyExists,
    LinkedAccountNotFound,
    NoImplementationFound,
    OAuth2Error,
    ProjectNotFound,
)
from aci.common.logging_setup import get_logger
from aci.common.schemas.linked_accounts import (
    LinkedAccountAPIKeyCreate,
    LinkedAccountDefaultCreate,
    LinkedAccountNoAuthCreate,
    LinkedAccountOAuth2Create,
    LinkedAccountOAuth2CreateState,
    LinkedAccountPublic,
    LinkedAccountsList,
    LinkedAccountUpdate,
)
from aci.common.schemas.security_scheme import (
    APIKeySchemeCredentials,
    NoAuthSchemeCredentials,
)
from aci.server import config, quota_manager
from aci.server import dependencies as deps
from aci.server import security_credentials_manager as scm
from aci.server.oauth2_manager import OAuth2Manager

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


@router.post("/default", response_model=LinkedAccountPublic, include_in_schema=False)
async def link_account_with_aci_default_credentials(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    body: Annotated[LinkedAccountDefaultCreate, Body()],
) -> LinkedAccount:
    """
    Create a linked account under an App using default credentials (e.g., API key, OAuth2, etc.)
    provided by ACI.
    If there is no default credentials provided by ACI for the specific App, the linked account will not be created,
    and an error will be returned.
    """
    logger.info(
        "Linking account with ACI default credentials",
        extra={
            "app_name": body.app_name,
            "linked_account_owner_id": body.linked_account_owner_id,
        },
    )
    # TODO: some duplicate code with other linked account creation routes
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, body.app_name
    )
    if not app_configuration:
        logger.error(
            "failed to link account with ACI default credentials, app configuration not found",
            extra={"app_name": body.app_name},
        )
        raise AppConfigurationNotFound(
            f"configuration for app={body.app_name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{body.app_name}"
        )

    # need to make sure the App actully has default credentials provided by ACI
    app_default_credentials = app_configuration.app.default_security_credentials_by_scheme.get(
        app_configuration.security_scheme
    )
    if not app_default_credentials:
        logger.error(
            "failed to link account with ACI default credentials, no default credentials provided by ACI",
            extra={
                "app_name": body.app_name,
                "security_scheme": app_configuration.security_scheme,
            },
        )
        # TODO: consider choosing a different exception type?
        raise NoImplementationFound(
            f"no default credentials provided by ACI for app={body.app_name}, "
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
        # TODO: support updating any type of linked account to use ACI default credentials
        logger.error(
            "failed to link account with ACI default credentials, linked account already exists",
            extra={
                "linked_account_owner_id": body.linked_account_owner_id,
                "app_name": body.app_name,
            },
        )
        raise LinkedAccountAlreadyExists(
            f"linked account with linked_account_owner_id={body.linked_account_owner_id} already exists for app={body.app_name}"
        )
    else:
        # Enforce linked accounts quota before creating new account
        quota_manager.enforce_linked_accounts_creation_quota(
            context.db_session, context.project.org_id, body.linked_account_owner_id
        )

        logger.info(
            "creating linked account with ACI default credentials",
            extra={
                "linked_account_owner_id": body.linked_account_owner_id,
                "app_name": body.app_name,
            },
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


@router.post("/no-auth", response_model=LinkedAccountPublic)
async def link_account_with_no_auth(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    body: LinkedAccountNoAuthCreate,
) -> LinkedAccount:
    """
    Create a linked account under an App that requires no authentication.
    """
    logger.info(
        "linking no_auth account",
        extra={
            "app_name": body.app_name,
            "linked_account_owner_id": body.linked_account_owner_id,
        },
    )
    # TODO: duplicate code with other linked account creation routes, refactor later
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, body.app_name
    )
    if not app_configuration:
        logger.error(
            "failed to link no_auth account, app configuration not found",
            extra={"app_name": body.app_name},
        )
        raise AppConfigurationNotFound(
            f"configuration for app={body.app_name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{body.app_name}"
        )
    if app_configuration.security_scheme != SecurityScheme.NO_AUTH:
        logger.error(
            "failed to link no_auth account, app configuration security scheme is not no_auth",
            extra={"app_name": body.app_name, "security_scheme": app_configuration.security_scheme},
        )
        raise NoImplementationFound(
            f"the security_scheme configured for app={body.app_name} is "
            f"{app_configuration.security_scheme}, not no_auth"
        )
    linked_account = crud.linked_accounts.get_linked_account(
        context.db_session,
        context.project.id,
        body.app_name,
        body.linked_account_owner_id,
    )
    if linked_account:
        logger.error(
            "failed to link no_auth account, linked account already exists",
            extra={
                "linked_account_owner_id": body.linked_account_owner_id,
                "app_name": body.app_name,
            },
        )
        raise LinkedAccountAlreadyExists(
            f"linked account with linked_account_owner_id={body.linked_account_owner_id} already exists for app={body.app_name}"
        )
    else:
        # Enforce linked accounts quota before creating new account
        quota_manager.enforce_linked_accounts_creation_quota(
            context.db_session, context.project.org_id, body.linked_account_owner_id
        )

        logger.info(
            "creating no_auth linked account",
            extra={
                "linked_account_owner_id": body.linked_account_owner_id,
                "app_name": body.app_name,
            },
        )
        linked_account = crud.linked_accounts.create_linked_account(
            context.db_session,
            context.project.id,
            body.app_name,
            body.linked_account_owner_id,
            SecurityScheme.NO_AUTH,
            NoAuthSchemeCredentials(),
            enabled=True,
        )

    context.db_session.commit()

    return linked_account


@router.post("/api-key", response_model=LinkedAccountPublic)
async def link_account_with_api_key(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    body: LinkedAccountAPIKeyCreate,
) -> LinkedAccount:
    """
    Create a linked account under an API key based App.
    """
    logger.info(
        "linking api_key account",
        extra={
            "app_name": body.app_name,
            "linked_account_owner_id": body.linked_account_owner_id,
        },
    )
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, body.app_name
    )
    if not app_configuration:
        logger.error(
            "failed to link api_key account, app configuration not found",
            extra={"app_name": body.app_name},
        )
        raise AppConfigurationNotFound(
            f"configuration for app={body.app_name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{body.app_name}"
        )
    # TODO: for now we require the security_schema used for accounts under an App must be the same as the security_schema configured in the app
    # configuration. But in the future, we might lift this restriction and allow any security_schema as long as the App supports it.
    if app_configuration.security_scheme != SecurityScheme.API_KEY:
        logger.error(
            f"failed to link api_key account, app configuration security scheme is "
            f"{app_configuration.security_scheme} instead of api_key",
            extra={
                "app_name": body.app_name,
                "security_scheme": app_configuration.security_scheme,
            },
        )
        # TODO: consider choosing a different exception type?
        raise NoImplementationFound(
            f"the security_scheme configured for app={body.app_name} is "
            f"{app_configuration.security_scheme}, not api_key"
        )
    linked_account = crud.linked_accounts.get_linked_account(
        context.db_session,
        context.project.id,
        body.app_name,
        body.linked_account_owner_id,
    )
    security_credentials = APIKeySchemeCredentials(
        secret_key=body.api_key,
    )
    # TODO: same as other linked account creation, we might want to separate the logic for updating and creating a linked account
    # or give warning to clients if the linked account already exists to avoid accidental overwriting the account
    if linked_account:
        # TODO: support updating api_key linked account
        logger.error(
            "failed to link api_key account, linked account already exists",
            extra={
                "linked_account_owner_id": body.linked_account_owner_id,
                "app_name": body.app_name,
            },
        )
        raise LinkedAccountAlreadyExists(
            f"linked account with linked_account_owner_id={body.linked_account_owner_id} already exists for app={body.app_name}"
        )
    else:
        # Enforce linked accounts quota before creating new account
        quota_manager.enforce_linked_accounts_creation_quota(
            context.db_session, context.project.org_id, body.linked_account_owner_id
        )

        logger.info(
            "creating api_key linked account",
            extra={
                "linked_account_owner_id": body.linked_account_owner_id,
                "app_name": body.app_name,
            },
        )
        linked_account = crud.linked_accounts.create_linked_account(
            context.db_session,
            context.project.id,
            body.app_name,
            body.linked_account_owner_id,
            SecurityScheme.API_KEY,
            security_credentials,
            enabled=True,
        )

    context.db_session.commit()

    return linked_account


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
        "Linking OAuth2 account",
        extra={
            "linked_account_oauth2_create": query_params.model_dump(exclude_none=True),
        },
    )
    app_configuration = crud.app_configurations.get_app_configuration(
        context.db_session, context.project.id, query_params.app_name
    )
    if not app_configuration:
        logger.error(
            "failed to link OAuth2 account, app configuration not found",
            extra={"app_name": query_params.app_name},
        )
        raise AppConfigurationNotFound(
            f"configuration for app={query_params.app_name} not found, please configure the app first {config.DEV_PORTAL_URL}/apps/{query_params.app_name}"
        )
    # TODO: for now we require the security_schema used for accounts under an App must be the same as the security_schema configured in the app
    # configuration. But in the future, we might lift this restriction and allow any security_schema as long the App supports it.
    if app_configuration.security_scheme != SecurityScheme.OAUTH2:
        logger.error(
            "failed to link OAuth2 account, app configuration security scheme is not OAuth2",
            extra={
                "app_name": query_params.app_name,
                "security_scheme": app_configuration.security_scheme,
            },
        )
        raise NoImplementationFound(
            f"the security_scheme configured in app={query_params.app_name} is "
            f"{app_configuration.security_scheme}, not OAuth2"
        )

    # Enforce linked accounts quota before creating new account
    quota_manager.enforce_linked_accounts_creation_quota(
        context.db_session, context.project.org_id, query_params.linked_account_owner_id
    )

    oauth2_scheme = scm.get_app_configuration_oauth2_scheme(
        app_configuration.app, app_configuration
    )

    oauth2_manager = OAuth2Manager(
        app_name=query_params.app_name,
        client_id=oauth2_scheme.client_id,
        client_secret=oauth2_scheme.client_secret,
        scope=oauth2_scheme.scope,
        authorize_url=oauth2_scheme.authorize_url,
        access_token_url=oauth2_scheme.access_token_url,
        refresh_token_url=oauth2_scheme.refresh_token_url,
        token_endpoint_auth_method=oauth2_scheme.token_endpoint_auth_method,
    )

    path = request.url_for(LINKED_ACCOUNTS_OAUTH2_CALLBACK_ROUTE_NAME).path
    redirect_uri = oauth2_scheme.redirect_url or f"{config.REDIRECT_URI_BASE}{path}"

    # create and encode the state payload.
    # NOTE: the state payload is jwt encoded (signed), but it's not encrypted, anyone can decode it
    # TODO: add expiration check to the state payload for extra security
    oauth2_state = LinkedAccountOAuth2CreateState(
        app_name=query_params.app_name,
        project_id=context.project.id,
        linked_account_owner_id=query_params.linked_account_owner_id,
        client_id=oauth2_scheme.client_id,
        redirect_uri=redirect_uri,
        code_verifier=OAuth2Manager.generate_code_verifier(),
        after_oauth2_link_redirect_url=query_params.after_oauth2_link_redirect_url,
    )
    oauth2_state_jwt = jwt.encode(
        {"alg": config.JWT_ALGORITHM},
        oauth2_state.model_dump(mode="json", exclude_none=True),
        config.SIGNING_KEY,
    ).decode()  # decode() is needed to convert the bytes to a string (not decoding the jwt payload) for this jwt library.

    authorization_url = await oauth2_manager.create_authorization_url(
        redirect_uri=redirect_uri,
        state=oauth2_state_jwt,
        code_verifier=oauth2_state.code_verifier,
    )

    logger.info(
        "authorization url",
        extra={"authorization_url": authorization_url},
    )

    # rewrite the authorization url for some apps that need special handling
    # TODO: this is hacky and need to refactor this in the future
    authorization_url = OAuth2Manager.rewrite_oauth2_authorization_url(
        query_params.app_name, authorization_url
    )

    logger.info(
        "authorization_url after rewriting",
        extra={"authorization_url": authorization_url},
    )
    return {"url": authorization_url}


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
    # check for errors
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description")
    if error:
        logger.error(
            "oauth2 account linking callback received, error",
            extra={"error": error, "error_description": error_description},
        )
        raise OAuth2Error(
            f"oauth2 account linking callback error: {error}, error_description: {error_description}"
        )

    # check for code
    code = request.query_params.get("code")
    if not code:
        logger.error(
            "oauth2 account linking callback received, missing code",
        )
        raise OAuth2Error("missing code parameter during account linking")

    # check for state
    state_jwt = request.query_params.get("state")
    if not state_jwt:
        logger.error(
            "oauth2 account linking callback received, missing state",
        )
        raise OAuth2Error("missing state parameter during account linking")

    # decode the state payload
    try:
        state = LinkedAccountOAuth2CreateState.model_validate(
            jwt.decode(state_jwt, config.SIGNING_KEY)
        )
        logger.info(
            "oauth2 account linking callback received, decoded state",
            extra={"state": state.model_dump(exclude_none=True)},
        )
    except Exception as e:
        logger.exception(
            f"failed to decode state_jwt, {e!s}",
            extra={"state_jwt": state_jwt},
        )
        raise AuthenticationError("invalid state parameter during account linking") from e

    # check if the app exists
    app = crud.apps.get_app(db_session, state.app_name, False, False)
    if not app:
        logger.error(
            "unable to continue with account linking, app not found",
            extra={"app_name": state.app_name},
        )
        raise AppNotFound(f"app={state.app_name} not found")

    # check app configuration
    # - exists
    # - configuration is OAuth2
    # - client_id matches the one used at the start of the OAuth2 flow
    app_configuration = crud.app_configurations.get_app_configuration(
        db_session, state.project_id, state.app_name
    )
    if not app_configuration:
        logger.error(
            "unable to continue with account linking, app configuration not found",
            extra={"app_name": state.app_name},
        )
        raise AppConfigurationNotFound(f"app configuration for app={state.app_name} not found")
    if app_configuration.security_scheme != SecurityScheme.OAUTH2:
        logger.error(
            "unable to continue with account linking, app configuration is not OAuth2",
            extra={"app_name": state.app_name},
        )
        raise NoImplementationFound(f"app configuration for app={state.app_name} is not OAuth2")

    # create oauth2 manager
    oauth2_scheme = scm.get_app_configuration_oauth2_scheme(
        app_configuration.app, app_configuration
    )
    if oauth2_scheme.client_id != state.client_id:
        logger.error(
            "unable to continue with account linking, client_id of state doesn't match client_id of app configuration",
            extra={
                "app_name": state.app_name,
                "client_id": oauth2_scheme.client_id,
                "state_client_id": state.client_id,
            },
        )
        raise OAuth2Error("client_id mismatch during account linking")

    oauth2_manager = OAuth2Manager(
        app_name=state.app_name,
        client_id=oauth2_scheme.client_id,
        client_secret=oauth2_scheme.client_secret,
        scope=oauth2_scheme.scope,
        authorize_url=oauth2_scheme.authorize_url,
        access_token_url=oauth2_scheme.access_token_url,
        refresh_token_url=oauth2_scheme.refresh_token_url,
        token_endpoint_auth_method=oauth2_scheme.token_endpoint_auth_method,
    )

    token_response = await oauth2_manager.fetch_token(
        redirect_uri=state.redirect_uri,
        code=code,
        code_verifier=state.code_verifier,
    )
    security_credentials = oauth2_manager.parse_fetch_token_response(token_response)

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
        logger.info(
            "updating oauth2 credentials for linked account",
            extra={"linked_account_id": linked_account.id},
        )
        linked_account = crud.linked_accounts.update_linked_account_credentials(
            db_session, linked_account, security_credentials
        )
    else:
        # Get the organization ID from the project
        project = crud.projects.get_project(db_session, state.project_id)
        if not project:
            logger.error(
                "project not found when creating linked account",
                extra={"project_id": state.project_id},
            )
            raise ProjectNotFound(f"Project with ID {state.project_id} not found")
        org_id = project.org_id
        # Enforce linked accounts quota before creating new account
        quota_manager.enforce_linked_accounts_creation_quota(
            db_session, org_id, state.linked_account_owner_id
        )

        logger.info(
            "creating oauth2 linked account",
            extra={
                "app_name": state.app_name,
                "linked_account_owner_id": state.linked_account_owner_id,
            },
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
@router.get("", response_model=list[LinkedAccountPublic])
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
        "listing linked accounts",
        extra={
            "linked_accounts_list": query_params.model_dump(exclude_none=True),
        },
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
    logger.info(
        "get linked account",
        extra={"linked_account_id": linked_account_id},
    )
    # validations
    linked_account = crud.linked_accounts.get_linked_account_by_id_under_project(
        context.db_session, linked_account_id, context.project.id
    )
    if not linked_account:
        logger.error(
            "linked account not found",
            extra={"linked_account_id": linked_account_id},
        )
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
    logger.info(
        "delete linked account",
        extra={"linked_account_id": linked_account_id},
    )
    linked_account = crud.linked_accounts.get_linked_account_by_id_under_project(
        context.db_session, linked_account_id, context.project.id
    )
    if not linked_account:
        logger.error(
            "linked account not found",
            extra={"linked_account_id": linked_account_id},
        )
        raise LinkedAccountNotFound(f"linked account={linked_account_id} not found")

    crud.linked_accounts.delete_linked_account(context.db_session, linked_account)

    context.db_session.commit()


@router.patch("/{linked_account_id}", response_model=LinkedAccountPublic)
async def update_linked_account(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    linked_account_id: UUID,
    body: LinkedAccountUpdate,
) -> LinkedAccount:
    """
    Update a linked account.
    """
    logger.info(
        "update linked account",
        extra={"linked_account_id": linked_account_id},
    )
    linked_account = crud.linked_accounts.get_linked_account_by_id_under_project(
        context.db_session, linked_account_id, context.project.id
    )
    if not linked_account:
        logger.error(
            "linked account not found",
            extra={"linked_account_id": linked_account_id},
        )
        raise LinkedAccountNotFound(f"linked account={linked_account_id} not found")

    linked_account = crud.linked_accounts.update_linked_account(
        context.db_session, linked_account, body
    )
    context.db_session.commit()

    return linked_account
