import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

# !For testing only.
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import User
from aipolabs.common.exceptions import UnexpectedError
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.user import UserCreate
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

    path = request.url_for("auth_callback", provider=provider.value).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
    logger.info(f"initiating login for provider={provider}, redirecting to={redirect_uri}")

    return await oauth2.authorize_redirect(oauth2_client, request, redirect_uri)


# callback route for different identity providers
# TODO: decision between long-lived JWT v.s session based v.s refresh token based auth
@router.get(
    "/callback/{provider}",
    name="auth_callback",
    include_in_schema=True,
)
async def auth_callback(
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
        user_info = auth_response["userinfo"]
    else:
        # TODO: implement other identity providers if added
        pass

    if not user_info["sub"]:
        logger.error(
            f"'sub' not found in user information for identity provider={provider}, "
            f"user_info={user_info}"
        )
        raise UnexpectedError(
            f"'sub' not found in user information for identity provider={provider}"
        )

    # Check if user already exists
    user = crud.users.get_user(
        db_session, identity_provider=user_info["iss"], user_id_by_provider=user_info["sub"]
    )
    if user:
        # Generate JWT token for the user
        # TODO: try/except, retry?
        jwt_token = create_access_token(
            str(user.id),
            timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        logger.debug(
            f"JWT generated successfully for user={user.id}, jwt_token={jwt_token[:4]}...{jwt_token[-4:]}"
        )
        response = RedirectResponse(url=f"{config.SERVER_DEV_PORTAL_URL}")
        response.set_cookie(
            key="accessToken",
            value=jwt_token,
            # httponly=True, # TODO: set after initial release
            # secure=True, # TODO: set after initial release
            samesite="lax",
            max_age=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return response
    else:
        # For new users, redirect to signup code page, passing along the user_info as needed.
        # For example, store user_info in session or use a temporary token.
        signup_redirect_url = (
            f"{config.SERVER_DEV_PORTAL_URL}/complete-signup?provider={provider.value}"
        )
        return RedirectResponse(url=signup_redirect_url)


# !For testing only. Define a model for the user info
class UserInfo(BaseModel):
    iss: str = Field(..., description="Issuer, e.g. https://accounts.google.com")
    sub: str = Field(
        ..., description="Unique identifier for the user provided by the identity provider"
    )
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    picture: str = Field(..., description="URL for the user's profile picture")


# !For testing only. Define the complete signup payload model
class CompleteSignupPayload(BaseModel):
    signup_code: str = Field(..., description="The signup code provided by the user")
    provider: str = Field(..., description="Identity provider, e.g. 'google'")
    user_info: UserInfo = Field(..., description="User info obtained from the identity provider")


@router.post("/complete-signup", include_in_schema=True)
async def complete_signup(
    # request: Request,
    data: CompleteSignupPayload,  # !For testing only
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse:
    """
    Endpoint to complete signup by verifying a signup code.
    Expected JSON payload:
    {
      "signup_code": "user entered code",
      "provider": "google",
      "user_info": { ... }  # user info from oauth callback, ideally securely passed via token/session
    }
    """
    # Global user cap from env variable, default to 5000
    max_users = int(os.getenv("MAX_USERS", "5000"))
    current_user_count = db_session.query(User).count()
    if current_user_count >= max_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Signups are currently closed. User limit reached.",
        )

    # data = await request.json()
    # signup_code = data.get("signup_code")
    signup_code = data.signup_code  # !For testing only
    if signup_code not in config.PERMITTED_SIGNUP_CODES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signup code.")

    # user_info = data.get("user_info")
    user_info = data.user_info  # !For testing only
    # if not user_info or not user_info.get("sub"):
    if not user_info or not user_info.sub:  # !For testing only
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user info.")

    # Create user record
    user = crud.users.create_user(
        db_session,
        UserCreate(
            identity_provider=user_info["iss"],
            user_id_by_provider=user_info["sub"],
            name=user_info["name"],
            email=user_info["email"],
            profile_picture=user_info["picture"],
        ),
    )
    _onboard_new_user(db_session, user)
    db_session.commit()

    # Generate JWT token and return or redirect
    jwt_token = create_access_token(
        str(user.id),
        timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.debug(
        f"JWT generated successfully for user={user.id}, jwt_token={jwt_token[:4]}...{jwt_token[-4:]}"
    )
    response = RedirectResponse(url=f"{config.SERVER_DEV_PORTAL_URL}")
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
