from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import User
from aipolabs.common.exceptions import AuthenticationError, UnexpectedError
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.user import IdentityProviderUserInfo, UserCreate
from aipolabs.server import config
from aipolabs.server import dependencies as deps
from aipolabs.server import oauth2

logger = get_logger(__name__)
# Create router instance
router = APIRouter()
oauth = OAuth()


class ClientIdentityProvider(str, Enum):
    GOOGLE = "google"
    # GITHUB = "github"


# oauth2 clients for our clients to login/signup with our developer portal
# TODO: is oauth2 client from authlib thread safe?
OAUTH2_CLIENTS: dict[ClientIdentityProvider, StarletteOAuth2App] = {
    ClientIdentityProvider.GOOGLE: oauth2.create_oauth2_client(
        name=ClientIdentityProvider.GOOGLE,
        client_id=config.GOOGLE_AUTH_CLIENT_ID,
        client_secret=config.GOOGLE_AUTH_CLIENT_SECRET,
        scope=config.GOOGLE_AUTH_CLIENT_SCOPE,
        server_metadata_url=config.GOOGLE_AUTH_SERVER_METADATA_URL,
    ),
}

LOGIN_CALLBACK_PATH_NAME = "auth_login_callback"
SIGNUP_CALLBACK_PATH_NAME = "auth_signup_callback"


# Function to generate JWT using Authlib
def create_access_token(user_id: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + expires_delta,
    }

    # Authlib expects a header, payload, and key
    header = {"alg": config.JWT_ALGORITHM}
    # TODO: try/except, retry?
    jwt_token: str = jwt.encode(
        header, payload, config.SIGNING_KEY
    ).decode()  # for this jwt lib, need to decode to convert bytes to string

    return jwt_token


# login route for different identity providers
@router.get("/login/{provider}", include_in_schema=True)
async def login(request: Request, provider: ClientIdentityProvider) -> RedirectResponse:
    oauth2_client = OAUTH2_CLIENTS[provider]

    path = request.url_for(LOGIN_CALLBACK_PATH_NAME, provider=provider.value).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
    logger.info(f"initiating login for provider={provider}, redirecting to={redirect_uri}")

    return await oauth2.authorize_redirect(oauth2_client, request, redirect_uri)


@router.get("/signup/{provider}", include_in_schema=True)
async def signup(
    request: Request,
    provider: ClientIdentityProvider,
    signup_code: str,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse:
    _validate_signup(db_session, signup_code)
    oauth2_client = OAUTH2_CLIENTS[provider]

    path = request.url_for(SIGNUP_CALLBACK_PATH_NAME, provider=provider.value).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}?signup_code={signup_code}"
    logger.info(
        f"initiating signup for provider={provider}, signup_code={signup_code}, redirecting to={redirect_uri}"
    )

    return await oauth2.authorize_redirect(oauth2_client, request, redirect_uri)


@router.get(
    "/signup/callback/{provider}",
    name=SIGNUP_CALLBACK_PATH_NAME,
    include_in_schema=True,
)
async def signup_callback(
    request: Request,
    response: Response,
    provider: ClientIdentityProvider,
    signup_code: str,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse:
    logger.info(
        f"signup callback received for identity provider={provider}, signup_code={signup_code}"
    )
    # TODO: probably not necessary to check again here, but just in case
    _validate_signup(db_session, signup_code)
    # TODO: try/except, retry?
    auth_response = await oauth2.authorize_access_token(OAUTH2_CLIENTS[provider], request)
    logger.debug(
        f"access token requested successfully for provider={provider}, "
        f"auth_response={auth_response}"
    )

    if provider == ClientIdentityProvider.GOOGLE:
        if "userinfo" not in auth_response:
            logger.error(f"userinfo not found in auth_response={auth_response}")
            raise UnexpectedError(f"userinfo not found in auth_response={auth_response}")
        user_info = IdentityProviderUserInfo.model_validate(auth_response["userinfo"])
    else:
        # TODO: implement other identity providers if added
        raise AuthenticationError(f"unsupported identity provider={provider}")

    user = crud.users.get_user(
        db_session, identity_provider=user_info.iss, user_id_by_provider=user_info.sub
    )
    # avoid duplicate signup
    if user:
        logger.error(
            f"user={user.id}, email={user.email} already exists for identity provider={provider}"
        )
        raise AuthenticationError(
            f"user={user.id}, email={user.email} already exists for identity provider={provider}"
        )

    user = crud.users.create_user(
        db_session,
        UserCreate(
            identity_provider=user_info.iss,
            user_id_by_provider=user_info.sub,
            name=user_info.name,
            email=user_info.email,
            profile_picture=user_info.picture,
        ),
    )
    _onboard_new_user(db_session, user)

    db_session.commit()
    logger.info(
        f"created new user={user.id}, email={user.email}, identity provider={provider}, signup_code={signup_code}"
    )
    # redirect to login page
    return RedirectResponse(url=f"{config.DEV_PORTAL_URL}/login")


# callback route for different identity providers
# TODO: decision between long-lived JWT v.s session based v.s refresh token based auth
@router.get(
    "/login/callback/{provider}",
    name=LOGIN_CALLBACK_PATH_NAME,
    include_in_schema=True,
)
async def login_callback(
    request: Request,
    response: Response,
    provider: ClientIdentityProvider,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse:
    logger.info(f"callback received for identity provider={provider}")
    # TODO: try/except, retry?
    auth_response = await oauth2.authorize_access_token(OAUTH2_CLIENTS[provider], request)
    logger.debug(
        f"access token requested successfully for provider={provider}, "
        f"auth_response={auth_response}"
    )

    if provider == ClientIdentityProvider.GOOGLE:
        if "userinfo" not in auth_response:
            logger.error(f"userinfo not found in auth_response={auth_response}")
            raise UnexpectedError(f"userinfo not found in auth_response={auth_response}")
        user_info = IdentityProviderUserInfo.model_validate(auth_response["userinfo"])
    else:
        # TODO: implement other identity providers if added
        raise AuthenticationError(f"unsupported identity provider={provider}")

    user = crud.users.get_user(
        db_session, identity_provider=user_info.iss, user_id_by_provider=user_info.sub
    )
    # redirect to signup page if user doesn't exist
    if not user:
        logger.error(f"user not found for identity provider={provider}, user_info={user_info}")
        return RedirectResponse(url=f"{config.DEV_PORTAL_URL}/signup")

    # Generate JWT token for the user
    # TODO: try/except, retry?
    jwt_token = create_access_token(
        str(user.id),
        timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.debug(
        f"JWT generated successfully for user={user.id}, jwt_token={jwt_token[:4]}...{jwt_token[-4:]}"
    )

    response = RedirectResponse(url=f"{config.DEV_PORTAL_URL}")
    response.set_cookie(
        key="accessToken",
        value=jwt_token,
        # httponly=True, # TODO: set after initial release
        # secure=True, # TODO: set after initial release
        samesite="lax",
        max_age=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


# TODO: For the Feb 2025 release, we decided to create default project (and agent, api key, app confiiguration, etc)
# for new users to decrease friction of onboarding. Need to revisit if we should keep this (or some of it)
# for the future releases.
def _onboard_new_user(db_session: Session, user: User) -> None:
    logger.info(f"onboarding new user={user.id}")
    project = crud.projects.create_project(db_session, owner_id=user.id, name="Default Project")
    logger.info(f"created default project={project.id} for user={user.id}")
    agent = crud.projects.create_agent(
        db_session,
        project.id,
        name="Default Agent",
        description="Default Agent",
        excluded_apps=[],
        excluded_functions=[],
        custom_instructions={},
    )
    logger.info(f"created default agent={agent.id} for project={project.id}")


def _validate_signup(db_session: Session, signup_code: str) -> None:
    if signup_code not in config.PERMITTED_SIGNUP_CODES:
        logger.error(f"invalid signup code={signup_code}")
        raise AuthenticationError(f"invalid signup code={signup_code}")

    total_users = crud.users.get_total_number_of_users(db_session)
    if total_users >= config.MAX_USERS:
        logger.error(
            f"max number of users={config.MAX_USERS} reached, signup failed with signup_code={signup_code}"
        )
        raise AuthenticationError(
            "no longer accepting new users, please email us contact@aipolabs.xyz if you still like to access"
        )
