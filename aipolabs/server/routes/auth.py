from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import APIRouter, Body, Depends, Request, Response, status
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
    logger.info("login", extra={"provider": provider.value})

    oauth2_client = OAUTH2_CLIENTS[provider]

    path = request.url_for(LOGIN_CALLBACK_PATH_NAME, provider=provider.value).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"

    logger.info(
        "authorizing login redirect",
        extra={"provider": provider.value, "redirect_uri": redirect_uri},
    )

    return await oauth2.authorize_redirect(oauth2_client, request, redirect_uri)


@router.post("/validate-signup-code", include_in_schema=True)
async def check_signup_code(
    signup_code: Annotated[str, Body(embed=True)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> Response:
    _validate_signup(db_session, signup_code)
    return Response(status_code=status.HTTP_200_OK)


@router.get("/signup/{provider}", include_in_schema=True)
async def signup(
    request: Request,
    provider: ClientIdentityProvider,
    signup_code: str,
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse:
    logger.info(
        "signup",
        extra={"provider": provider.value, "signup_code": signup_code},
    )
    _validate_signup(db_session, signup_code)
    oauth2_client = OAUTH2_CLIENTS[provider]

    request.session["signup_code"] = signup_code

    path = request.url_for(SIGNUP_CALLBACK_PATH_NAME, provider=provider.value).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
    logger.info(
        "authorizing signup redirect",
        extra={
            "provider": provider.value,
            "signup_code": signup_code,
            "redirect_uri": redirect_uri,
        },
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
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse:
    if "signup_code" not in request.session:
        logger.error("no signup_code in session")
        raise AuthenticationError("no signup_code in session")

    signup_code = request.session["signup_code"]
    del request.session["signup_code"]  # Clear session data after use

    logger.info(
        "signup callback received",
        extra={"provider": provider.value, "signup_code": signup_code},
    )
    # TODO: probably not necessary to check again here, but just in case
    _validate_signup(db_session, signup_code)
    # TODO: try/except, retry?
    auth_response = await oauth2.authorize_access_token(OAUTH2_CLIENTS[provider], request)
    logger.debug(
        "access token requested successfully",
        extra={"provider": provider.value, "auth_response": auth_response},
    )

    if provider == ClientIdentityProvider.GOOGLE:
        if "userinfo" not in auth_response:
            logger.error(
                "userinfo not found in auth_response",
                extra={"auth_response": auth_response},
            )
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
        logger.warning(
            "duplicate signup, user already exists",
            extra={"user_id": user.id},
        )
    else:
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
            "created new user",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "provider": provider.value,
                "signup_code": signup_code,
            },
        )

    jwt_token = create_access_token(
        str(user.id),
        timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.debug(
        f"JWT generated successfully for user={user.id}, jwt_token={jwt_token[:4]}...{jwt_token[-4:]}"
    )

    response = RedirectResponse(url=f"{config.DEV_PORTAL_URL}")
    response.set_cookie(
        # TODO: need to get rid of this when we switch to secure http cookie authentication
        # Allow the dev portal domain to see the cookie as well
        domain=config.AIPOLABS_ROOT_DOMAIN,
        key=config.COOKIE_KEY_FOR_AUTH_TOKEN,
        value=jwt_token,
        # httponly=True, # TODO: set after initial release
        # secure=True, # TODO: set after initial release
        samesite="lax",
        max_age=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


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
    logger.info(
        "login callback received",
        extra={"provider": provider.value},
    )
    # TODO: try/except, retry?
    auth_response = await oauth2.authorize_access_token(OAUTH2_CLIENTS[provider], request)
    logger.debug(
        "access token requested successfully",
        extra={"provider": provider.value, "auth_response": auth_response},
    )

    if provider == ClientIdentityProvider.GOOGLE:
        if "userinfo" not in auth_response:
            logger.error(
                "userinfo not found in auth_response",
                extra={"auth_response": auth_response},
            )
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
        logger.error(
            "login failed, user not found",
            extra={
                "provider": provider.value,
                "user_info": user_info.model_dump(exclude_none=True),
            },
        )
        # TODO: Return a cookie to signal the frontend that the user hasn't logged
        return RedirectResponse(url=f"{config.DEV_PORTAL_URL}")

    # Generate JWT token for the user
    # TODO: try/except, retry?
    jwt_token = create_access_token(
        str(user.id),
        timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.debug(
        "JWT generated successfully",
        extra={"user_id": user.id, "jwt_token": jwt_token[:4] + "..." + jwt_token[-4:]},
    )

    response = RedirectResponse(url=f"{config.DEV_PORTAL_URL}")
    response.set_cookie(
        # TODO: need to get rid of this when we switch to secure http cookie authentication
        # Allow the dev portal domain to see the cookie as well
        domain=config.AIPOLABS_ROOT_DOMAIN,
        key=config.COOKIE_KEY_FOR_AUTH_TOKEN,
        value=jwt_token,
        # httponly=True, # TODO: set after initial release
        # secure=True, # TODO: set after initial release
        samesite="lax",
        max_age=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.post("/logout", include_in_schema=True)
async def logout() -> Response:
    response = Response(status_code=status.HTTP_200_OK)
    response.delete_cookie(
        key=config.COOKIE_KEY_FOR_AUTH_TOKEN,
        domain=config.AIPOLABS_ROOT_DOMAIN,
        samesite="lax",
    )
    return response


# TODO: For the Feb 2025 release, we decided to create default project (and agent, api key, app confiiguration, etc)
# for new users to decrease friction of onboarding. Need to revisit if we should keep this (or some of it)
# for the future releases.
def _onboard_new_user(db_session: Session, user: User) -> None:
    logger.info(
        "onboarding new user",
        extra={"user_id": user.id},
    )
    project = crud.projects.create_project(db_session, owner_id=user.id, name="Default Project")
    logger.info(
        "created default project",
        extra={"project_id": project.id, "user_id": user.id},
    )
    agent = crud.projects.create_agent(
        db_session,
        project.id,
        name="Default Agent",
        description="Default Agent",
        excluded_apps=[],
        excluded_functions=[],
        custom_instructions={},
    )
    logger.info(
        "created default agent",
        extra={"agent_id": agent.id, "project_id": project.id, "user_id": user.id},
    )


def _validate_signup(db_session: Session, signup_code: str) -> None:
    if signup_code not in config.PERMITTED_SIGNUP_CODES:
        logger.error(
            "invalid signup code",
            extra={"signup_code": signup_code},
        )
        raise AuthenticationError(f"invalid signup code={signup_code}")

    total_users = crud.users.get_total_number_of_users(db_session)
    if total_users >= config.MAX_USERS:
        logger.error(
            "max number of users reached",
            extra={"signup_code": signup_code, "total_users": total_users},
        )
        raise AuthenticationError(
            "no longer accepting new users, please email us support@aipolabs.xyz if you still like to access"
        )
