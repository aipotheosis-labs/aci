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
    """
    Generate a JWT access token for the given user.
    
    This function creates a JSON Web Token (JWT) that includes the following claims:
    - "sub": the subject identifier set to the provided user_id,
    - "iat": the issued-at time set to the current UTC time,
    - "exp": the expiration time computed as the current UTC time plus the provided expires_delta.
    
    The JWT is encoded using the header that specifies the algorithm defined in the configuration (config.JWT_ALGORITHM)
    and is signed using the signing key (config.SIGNING_KEY). The resulting token, initially in bytes, is decoded to a string
    before being returned.
    
    Parameters:
        user_id (str): The unique identifier for the user.
        expires_delta (timedelta): The duration after which the token should expire.
    
    Returns:
        str: The encoded JWT access token as a string.
    """
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
    """
    Initiates the OAuth2 login process for the specified identity provider and redirects the user to the provider's authorization page.
    
    This function constructs a callback URI by combining the base redirect URI from configuration with the dynamically generated path for the login callback. It logs the initiation of the login process and then calls the OAuth2 client's authorize_redirect method to perform the redirection.
    
    Parameters:
        request (Request): The incoming HTTP request used to generate the callback URL.
        provider (ClientIdentityProvider): The identity provider (e.g., Google) to authenticate against.
    
    Returns:
        RedirectResponse: An asynchronous response that redirects the user to the OAuth2 provider's authorization endpoint.
    """
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
    """
    Asynchronously initiates the signup process by validating the provided signup code and redirecting the user to the OAuth2 provider's authorization page.
    
    This function first validates the signup code against permitted values and user limits using the given database session. It then constructs a redirect URI for the OAuth2 signup callback, appending the signup code as a query parameter. An informational log is recorded before the function asynchronously redirects the user to the OAuth2 provider's authorization endpoint.
    
    Parameters:
        request (Request): The incoming request object.
        provider (ClientIdentityProvider): The identity provider to use for OAuth2 signup (e.g., Google).
        signup_code (str): Code used to validate and authorize the signup process.
        db_session (Annotated[Session, Depends(deps.yield_db_session)]): The database session used for validating the signup code.
    
    Returns:
        RedirectResponse: A response object that redirects the user to the OAuth2 provider's authorization endpoint.
    
    Raises:
        AuthenticationError: If the signup code validation fails due to an invalid code or exceeding user limits.
    """
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
    """
    Processes the signup callback from an OAuth2 identity provider to register a new user.
    
    This asynchronous function handles the callback after a user initiates signup via an identity provider (currently, only Google is supported). It validates the provided signup code, retrieves an access token, and extracts user information from the OAuth2 provider's response. If the user already exists, it raises an AuthenticationError; otherwise, it creates a new user, onboards them by setting up default projects and agents, and finally redirects the client to the login page.
    
    Parameters:
        request (Request): The incoming HTTP request containing callback data.
        response (Response): The HTTP response object to be modified as needed.
        provider (ClientIdentityProvider): The identity provider used for signup (only Google is supported).
        signup_code (str): The code used to validate the signup process.
        db_session (Session): A database session provided via dependency injection for performing CRUD operations.
    
    Returns:
        RedirectResponse: A redirect response to the login page after successful user registration.
    
    Raises:
        AuthenticationError: If the identity provider is unsupported or the user already exists.
        UnexpectedError: If the OAuth2 response does not contain required user information.
    """
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
    """
    Process the callback for user login via an OAuth2 identity provider.
    
    This asynchronous function handles the callback endpoint used after a user
    attempts to authenticate with an identity provider (e.g., Google). It retrieves
    the access token and user information from the provider's authorization response.
    For Google, if the 'userinfo' field is missing in the response, an UnexpectedError is raised.
    If the provider is not supported, an AuthenticationError is raised.
    
    After successfully extracting the user information, the function attempts to retrieve
    the corresponding user from the database. If the user does not exist, the function logs
    an error and redirects the client to the signup page. Otherwise, it generates a JWT token
    using the user's ID, sets it as a cookie in the response, and redirects the client to the
    development portal.
    
    Parameters:
        request (Request): The incoming HTTP request.
        response (Response): The HTTP response object used to set cookies and handle redirects.
        provider (ClientIdentityProvider): The identity provider (e.g., Google) initiating the callback.
        db_session (Session): A database session provided via FastAPI's dependency injection.
    
    Returns:
        RedirectResponse: A redirect response directing the user to either the development portal
                          (on successful authentication) or the signup page (if the user is not found).
    
    Raises:
        UnexpectedError: If the authentication response from the identity provider lacks the 'userinfo' key.
        AuthenticationError: If an unsupported identity provider is specified.
    """
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
    """
    Onboard a new user by creating a default project and agent.
    
    This function logs the initialization of the onboarding process for a new user by performing the following steps:
    1. Logging the start of the onboarding.
    2. Creating a default project owned by the user.
    3. Logging the creation of the default project.
    4. Creating a default agent within the created project with preset parameters.
    5. Logging the creation of the default agent.
    
    Parameters:
        db_session (Session): The active database session used to interact with the database.
        user (User): The user to be onboarded; must have a valid `id` attribute.
    
    Returns:
        None
    """
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
    """
    Validate the provided signup code and enforce the maximum user limit.
    
    This function ensures that the signup code is among the permitted codes specified in the configuration.
    If the code is invalid, it logs an error and raises an AuthenticationError.
    Additionally, it checks that the total number of users in the database has not reached the maximum limit.
    If the limit is reached, it logs an error and raises an AuthenticationError indicating that no new users can be accepted.
    
    Parameters:
        db_session (Session): The database session used to query the current total number of users.
        signup_code (str): The signup code provided during the signup process.
    
    Raises:
        AuthenticationError: If the provided signup code is invalid or if the maximum number of users has been reached.
    """
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
