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
    response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/login/unsupported")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_signup_with_invalid_signup_code(test_client: TestClient) -> None:
    INVALID_SIGNUP_CODE = "invalid"
    response = test_client.get(
        f"{config.ROUTER_PREFIX_AUTH}/signup/google?signup_code={INVALID_SIGNUP_CODE}"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid signup code=" in response.json()["error"]


def test_signup_with_valid_signup_code(test_client: TestClient) -> None:
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
