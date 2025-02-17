import uuid
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from authlib.jose import jwt
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, User
from aipolabs.common.schemas.user import IdentityProviderUserInfo, UserCreate
from aipolabs.server import config

MOCK_USER_GOOGLE_AUTH_DATA = {
    "userinfo": {
        "sub": "123",
        "iss": "mock_google",
        "name": "Test User",
        "email": "test@example.com",
        "picture": "http://example.com/pic.jpg",
    }
}
MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
    f"client_id={config.GOOGLE_AUTH_CLIENT_ID}&"
    "redirect_uri"
)


def test_login_google(test_client: TestClient) -> None:
    # This is a redirect response, but we are not following the redirect
    # (set follow_redirects=False when creating the test client)
    """
    Test the Google login endpoint for proper redirection.
    
    This test verifies that the Google login endpoint returns an HTTP 302 redirection response
    with a location header formatted to initiate the OAuth flow. It specifically checks that:
    - The "redirect_uri" query parameter in the redirection URL matches the expected callback URL.
    - The location header starts with the expected Google OAuth redirect URI prefix.
    - The response status code is HTTP 302 Found.
    
    Parameters:
        test_client (TestClient): A FastAPI TestClient instance configured with follow_redirects set to False.
    """
    response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/login/google")
    location = response.headers["location"]
    redirect_uri = parse_qs(urlparse(location).query)["redirect_uri"][0]

    assert (
        redirect_uri
        == f"{config.AIPOLABS_REDIRECT_URI_BASE}{config.ROUTER_PREFIX_AUTH}/login/callback/google"
    )
    assert response.headers["location"].startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    assert response.status_code == status.HTTP_302_FOUND


# mock_oauth_provider to mock google Oauth user info
def test_login_callback_google_user_exists(
    test_client: TestClient, db_session: Session, dummy_apps: list[App]
) -> None:
    # create a user
    """
    Test the Google login callback for an existing user.
    
    This test simulates a scenario where a user already exists in the database and completes the Google OAuth callback flow. A mock user is created in the database, and the OAuth2 client's token retrieval method is patched to return predefined Google authentication data. The test then sends a GET request to the login callback endpoint and asserts that:
      - The response is a Temporary Redirect (HTTP 307).
      - An "accessToken" cookie is present in the response.
      - The JWT contained in the "accessToken" cookie is correctly decoded and validated.
      - The "sub" claim in the JWT payload matches the ID of the created mock user.
    
    Parameters:
        test_client (TestClient): FastAPI test client used to send HTTP requests.
        db_session (Session): SQLAlchemy session for database operations in tests.
        dummy_apps (list[App]): List of dummy App instances to satisfy dependencies during testing.
    
    Returns:
        None
    
    Raises:
        AssertionError: If any of the assertions regarding the response status, cookie presence, or JWT claims fail.
    """
    mock_user = _create_mock_user(db_session)
    # mock the oauth2 client's authorize_access_token method
    with patch(
        "aipolabs.server.oauth2.authorize_access_token",
        return_value=MOCK_USER_GOOGLE_AUTH_DATA,
    ):
        response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/login/callback/google")

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

    accessToken = response.cookies.get("accessToken")

    # check jwt token is generated
    assert accessToken is not None
    # check user is created
    payload = jwt.decode(accessToken, config.SIGNING_KEY)
    payload.validate()
    user_id = payload.get("sub")
    # get user by id and check user is created

    assert user_id == str(mock_user.id)


def test_login_callback_google_user_does_not_exist(test_client: TestClient) -> None:
    # mock the oauth2 client's authorize_access_token method
    with patch(
        "aipolabs.server.oauth2.authorize_access_token",
        return_value=MOCK_USER_GOOGLE_AUTH_DATA,
    ):
        response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/login/callback/google")

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert (
        response.headers["location"] == f"{config.DEV_PORTAL_URL}/signup"
    ), "should redirect to signup page if user does not exist"


def test_login_unsupported_provider(test_client: TestClient) -> None:
    """
    Test the login endpoint with an unsupported provider.
    
    This test sends a GET request to the login endpoint using an unsupported provider
    and verifies that the server returns a 422 Unprocessable Entity status code,
    indicating that the provider is not supported.
    
    Parameters:
        test_client (TestClient): The FastAPI test client used to simulate HTTP requests.
    """
    response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/login/unsupported")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_signup_with_invalid_signup_code(test_client: TestClient) -> None:
    """
    Test the signup endpoint with an invalid signup code.
    
    This test sends a GET request to the Google signup endpoint using an invalid code,
    verifying that the server responds with an HTTP 401 Unauthorized status. It also
    checks that the returned error message contains an indication of the invalid signup code.
    
    Parameters:
        test_client (TestClient): A FastAPI test client for sending HTTP requests.
    
    Returns:
        None
    """
    INVALID_SIGNUP_CODE = "invalid"
    response = test_client.get(
        f"{config.ROUTER_PREFIX_AUTH}/signup/google?signup_code={INVALID_SIGNUP_CODE}"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid signup code=" in response.json()["error"]


def test_signup_with_valid_signup_code(test_client: TestClient) -> None:
    """
    Test the signup endpoint with a valid signup code.
    
    This test sends a GET request to the Google signup endpoint using a valid signup code from the permitted signup codes.
    It verifies that:
      - The response has an HTTP 302 Found status, indicating a redirection.
      - The "location" header in the response begins with the expected Google OAuth redirect URI prefix.
      - The 'redirect_uri' query parameter extracted from the redirection URL matches the expected callback URL,
        which is constructed using the application’s base redirect URI, the authentication router prefix, and includes the signup code.
    
    Parameters:
        test_client (TestClient): A configured FastAPI test client for simulating HTTP requests.
    
    Returns:
        None
    """
    VALID_SIGNUP_CODE = config.PERMITTED_SIGNUP_CODES[0]
    response = test_client.get(
        f"{config.ROUTER_PREFIX_AUTH}/signup/google?signup_code={VALID_SIGNUP_CODE}"
    )

    assert response.status_code == status.HTTP_302_FOUND

    location = response.headers["location"]
    redirect_uri = parse_qs(urlparse(location).query)["redirect_uri"][0]

    assert location.startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    assert (
        redirect_uri
        == f"{config.AIPOLABS_REDIRECT_URI_BASE}{config.ROUTER_PREFIX_AUTH}/signup/callback/google?signup_code={VALID_SIGNUP_CODE}"
    )


def test_signup_max_users_reached(test_client: TestClient, db_session: Session) -> None:
    # create random max number of users
    """
    Test the signup callback behavior when the maximum number of users has been reached.
    
    This test simulates a condition where the database already contains the maximum allowed users defined by config.MAX_USERS. It creates dummy users using randomized data, commits them to the database, and then attempts to execute a signup callback using a valid signup code. The test asserts that the response returns an HTTP 401 Unauthorized status and includes an error message stating that no new users are being accepted.
        
    Parameters:
        test_client (TestClient): A FastAPI TestClient used to simulate HTTP requests.
        db_session (Session): Database session for database operations.
    
    Returns:
        None
    """
    for _ in range(config.MAX_USERS):
        crud.users.create_user(
            db_session,
            UserCreate(
                identity_provider="mock_google",
                user_id_by_provider=str(uuid.uuid4()),
                name=f"Test User {uuid.uuid4()}",
                email=f"test{uuid.uuid4()}@example.com",
                profile_picture=f"http://example.com/pic{uuid.uuid4()}.jpg",
            ),
        )
    db_session.commit()

    # try to signup
    VALID_SIGNUP_CODE = config.PERMITTED_SIGNUP_CODES[0]
    response = test_client.get(
        f"{config.ROUTER_PREFIX_AUTH}/signup/callback/google?signup_code={VALID_SIGNUP_CODE}"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "no longer accepting new users" in response.json()["error"]


def test_signup_callback_google(
    test_client: TestClient, db_session: Session, dummy_apps: list[App]
) -> None:
    """
    Test the Google signup callback endpoint to ensure proper user creation and default entity setup.
    
    This test simulates a callback from Google OAuth during the signup process using a valid signup code.
    It patches the external OAuth token retrieval to return predetermined mock user data. The test verifies
    that the endpoint responds with an HTTP 307 Temporary Redirect to the login page after signup. It then
    checks that a new user is created in the database with the correct identity provider user information and that
    the associated default entities (a project with an agent and an API key) are successfully created.
    
    Parameters:
        test_client (TestClient): FastAPI test client for making HTTP requests.
        db_session (Session): Database session for verifying user creation and associated entities.
        dummy_apps (list[App]): List of dummy applications required for initializing default settings (not used directly).
    
    Returns:
        None
    
    Raises:
        AssertionError: If the response status, redirect URL, user creation, or default entity setup does not match expectations.
    """
    VALID_SIGNUP_CODE = config.PERMITTED_SIGNUP_CODES[0]
    with patch(
        "aipolabs.server.oauth2.authorize_access_token",
        return_value=MOCK_USER_GOOGLE_AUTH_DATA,
    ):
        response = test_client.get(
            f"{config.ROUTER_PREFIX_AUTH}/signup/callback/google?signup_code={VALID_SIGNUP_CODE}"
        )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert (
        response.headers["location"] == f"{config.DEV_PORTAL_URL}/login"
    ), "should redirect to login after signup"

    # get user by id and check user is created
    identity_provider_user_info = IdentityProviderUserInfo.model_validate(
        MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]
    )
    user = crud.users.get_user(
        db_session,
        identity_provider=identity_provider_user_info.iss,
        user_id_by_provider=identity_provider_user_info.sub,
    )
    assert user is not None
    assert user.identity_provider == identity_provider_user_info.iss
    assert user.user_id_by_provider == identity_provider_user_info.sub
    assert user.email == identity_provider_user_info.email
    assert user.name == identity_provider_user_info.name
    assert user.profile_picture == identity_provider_user_info.picture

    # check defaults (project, agent, api key) are created
    projects = crud.projects.get_projects_by_owner(db_session, user.id)
    assert len(projects) == 1
    project = projects[0]
    assert len(project.agents) == 1
    agent = project.agents[0]
    assert len(agent.api_keys) == 1


def test_signup_callback_google_user_already_exists(
    test_client: TestClient, db_session: Session, dummy_apps: list[App]
) -> None:
    VALID_SIGNUP_CODE = config.PERMITTED_SIGNUP_CODES[0]

    user: User = _create_mock_user(db_session)

    with patch(
        "aipolabs.server.oauth2.authorize_access_token",
        return_value=MOCK_USER_GOOGLE_AUTH_DATA,
    ):
        response = test_client.get(
            f"{config.ROUTER_PREFIX_AUTH}/signup/callback/google?signup_code={VALID_SIGNUP_CODE}"
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert f"user={user.id}, email={user.email} already exists" in response.json()["error"]


def _create_mock_user(db_session: Session) -> User:
    """
    Creates a mock user in the database using sample Google OAuth data.
    
    This function validates the Google OAuth user information from MOCK_USER_GOOGLE_AUTH_DATA and creates a new user record by invoking the create_user method on the users CRUD interface. The new user is then committed to the database using the provided session, simulating the OAuth user creation process during tests.
    
    Parameters:
        db_session (Session): An active SQLAlchemy session for database operations.
    
    Returns:
        User: The newly created user object with details populated from the validated OAuth user info.
    
    Side Effects:
        Commits the new user record to the database.
    """
    identity_provider_user_info = IdentityProviderUserInfo.model_validate(
        MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]
    )
    user = crud.users.create_user(
        db_session,
        UserCreate(
            identity_provider=identity_provider_user_info.iss,
            user_id_by_provider=identity_provider_user_info.sub,
            name=identity_provider_user_info.name,
            email=identity_provider_user_info.email,
            profile_picture=identity_provider_user_info.picture,
        ),
    )
    db_session.commit()
    return user
