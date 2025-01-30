from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from authlib.jose import jwt
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App
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
        == f"{config.AIPOLABS_REDIRECT_URI_BASE}{config.ROUTER_PREFIX_AUTH}/callback/google"
    )
    assert response.headers["location"].startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    assert response.status_code == status.HTTP_302_FOUND


# mock_oauth_provider to mock google Oauth user info
def test_callback_google(
    test_client: TestClient, db_session: Session, dummy_apps: list[App]
) -> None:
    # mock the oauth2 client's authorize_access_token method
    with patch(
        "aipolabs.server.oauth2.authorize_access_token",
        return_value=MOCK_USER_GOOGLE_AUTH_DATA,
    ):
        response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/callback/google")

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

    accessToken = response.cookies.get("accessToken")

    # check jwt token is generated
    assert accessToken is not None
    # check user is created
    payload = jwt.decode(accessToken, config.SIGNING_KEY)
    payload.validate()
    user_id = payload.get("sub")
    # get user by id and check user is created

    user = crud.users.get_user_by_id(db_session, user_id)
    assert user is not None
    assert user.identity_provider == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["iss"]
    assert user.user_id_by_provider == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["sub"]
    assert user.email == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["email"]
    assert user.name == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["name"]
    assert user.profile_picture == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["picture"]

    # check defaults (project, agent, api key) are created
    projects = crud.projects.get_projects_by_owner(db_session, user_id)
    assert len(projects) == 1
    project = projects[0]
    assert len(project.agents) == 1
    agent = project.agents[0]
    assert len(agent.api_keys) == 1


def test_login_unsupported_provider(test_client: TestClient) -> None:
    response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/login/unsupported")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
