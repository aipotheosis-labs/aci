from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Any, cast

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from authlib.jose import JoseError, jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.user import AuthResponse, UserCreate
from aipolabs.server import config
from aipolabs.server import dependencies as deps

logger = get_logger(__name__)
# Create router instance
router = APIRouter()
oauth = OAuth()


class AuthProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"


# Register Google OAuth
oauth.register(
    name=AuthProvider.GOOGLE,
    client_id=config.GOOGLE_AUTH_CLIENT_ID,
    client_secret=config.GOOGLE_AUTH_CLIENT_SECRET,
    client_kwargs=config.GOOGLE_AUTH_CLIENT_KWARGS,
    server_metadata_url=config.GOOGLE_AUTH_SERVER_METADATA_URL,
)


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
    try:
        jwt_token: str = jwt.encode(
            header, payload, config.JWT_SECRET_KEY
        ).decode()  # Decode to convert bytes to string

        return jwt_token
    except JoseError as e:
        logger.error(f"JWT generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="JWT generation failed")


# login route for different auth providers
@router.get("/login/{provider}", include_in_schema=False)
async def login(request: Request, provider: str) -> Any:
    if provider not in oauth._registry:
        logger.error(f"Unsupported provider: {provider}")
        raise HTTPException(status_code=400, detail="Unsupported provider")

    path = request.url_for("auth_callback", provider=provider).path
    redirect_uri = f"{config.AIPOLABS_REDIRECT_URI_BASE}{path}"
    logger.info(f"Initiating OAuth login for provider: {provider}, redirecting to: {redirect_uri}")
    oauth_client = cast(StarletteOAuth2App, oauth.create_client(provider))

    return await oauth_client.authorize_redirect(request, redirect_uri)


# callback route for different auth providers
# TODO: decision between long-lived JWT v.s session based v.s refresh token based auth
@router.get(
    "/callback/{provider}",
    name="auth_callback",
    response_model=AuthResponse,
    include_in_schema=False,
)
async def auth_callback(
    request: Request, provider: str, db_session: Annotated[Session, Depends(deps.yield_db_session)]
) -> Any:
    logger.info(f"Callback received for provider: {provider}")
    if provider not in oauth._registry:
        logger.error(f"Unsupported provider during callback: {provider}")
        raise HTTPException(status_code=400, detail="Unsupported provider")

    oauth_client = cast(StarletteOAuth2App, oauth.create_client(provider))

    try:
        logger.info(f"Retrieving access token for provider: {provider}")
        auth_response = await oauth_client.authorize_access_token(request)
        logger.debug(
            f"Access token requested successfully for provider: {provider}, "
            f"auth_response: {auth_response}"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve access token for provider {provider}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to retrieve access token: {str(e)}")

    if provider == AuthProvider.GOOGLE.value:
        user_info = auth_response["userinfo"]
    else:
        pass

    if not user_info["sub"]:
        logger.error(f"User ID not found in user information for provider {provider}")
        raise HTTPException(status_code=400, detail="User ID not found from auth provider")

    try:
        user = crud.get_or_create_user(
            db_session,
            UserCreate(
                auth_provider=user_info["iss"],
                auth_user_id=user_info["sub"],
                name=user_info["name"],
                email=user_info["email"],
                profile_picture=user_info["picture"],
            ),
        )
        db_session.commit()
    except Exception as e:
        # TODO: remove PII log
        logger.error(f"Failed to create or get user: {user_info}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"auth failed: {str(e)}",
        )

    # Generate JWT token for the user
    try:
        jwt_token = create_access_token(
            str(user.id),
            timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        logger.debug(
            f"JWT generated successfully for user: {user.id}, jwt_token: {jwt_token[:4]}...{jwt_token[-4:]}"
        )
    except Exception:
        logger.error(f"JWT generation failed for user {user.id}", exc_info=True)
        raise HTTPException(status_code=500, detail="JWT generation failed")

    return AuthResponse(access_token=jwt_token, token_type="bearer", user_id=user.id)
