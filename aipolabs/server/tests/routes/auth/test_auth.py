from unittest.mock import patch

from authlib.integrations.starlette_client import StarletteOAuth2App
from authlib.jose import jwt
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import User
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
    assert response.headers["location"].startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    assert response.status_code == status.HTTP_302_FOUND


# mock_oauth_provider to mock google Oauth user info
def test_callback_google(test_client: TestClient, db_session: Session) -> None:
    # mock the oauth2 client's authorize_access_token method
    with patch.object(
        StarletteOAuth2App,
        "authorize_access_token",
        return_value=MOCK_USER_GOOGLE_AUTH_DATA,
    ):
        response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/callback/google")

    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    # check jwt token is generated
    assert data["access_token"] is not None
    assert data["token_type"] == "bearer"
    # check user is created
    payload = jwt.decode(data["access_token"], config.JWT_SECRET_KEY)
    payload.validate()
    user_id = payload.get("sub")
    # get user by id and check user is created

    user = db_session.execute(select(User).filter(User.id == user_id)).scalar_one_or_none()
    assert user is not None
    assert user.identity_provider == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["iss"]
    assert user.user_id_by_provider == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["sub"]
    assert user.email == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["email"]
    assert user.name == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["name"]
    assert user.profile_picture == MOCK_USER_GOOGLE_AUTH_DATA["userinfo"]["picture"]

    # Clean up: Delete the created user
    db_session.delete(user)
    db_session.commit()


def test_login_unsupported_provider(test_client: TestClient) -> None:
    response = test_client.get(f"{config.ROUTER_PREFIX_AUTH}/login/unsupported")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert str(response.json()["error"]).startswith("Unsupported identity provider")
