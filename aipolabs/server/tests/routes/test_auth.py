import pytest
from authlib.jose import jwt
from fastapi import Request, status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
from aipolabs.server import config

MOCK_USER_GOOGLE_AUTH_DATA = {
    "sub": "123",
    "iss": "mock_google",
    "name": "Test User",
    "email": "test@example.com",
    "picture": "http://example.com/pic.jpg",
}
MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
    f"client_id={config.GOOGLE_AUTH_CLIENT_ID}&"
    "redirect_uri"
)


@pytest.fixture
def mock_oauth_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockOAuthClient:
        async def authorize_access_token(self, request: Request) -> dict[str, dict]:
            return {"userinfo": MOCK_USER_GOOGLE_AUTH_DATA}

    # Mock the OAuth client creation
    def mock_create_client(provider: str) -> MockOAuthClient:
        return MockOAuthClient()

    # Mock the OAuth provider registry
    monkeypatch.setattr(
        "aipolabs.server.routes.auth.oauth._registry", {"google": "mock_google_client"}
    )
    monkeypatch.setattr("aipolabs.server.routes.auth.oauth.create_client", mock_create_client)


def test_login_google(test_client: TestClient) -> None:
    # This is a redirect response, but we are not following the redirect
    # (set follow_redirects=False when creating the test client)
    response = test_client.get("/v1/auth/login/google")
    assert response.headers["location"].startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    assert response.status_code == status.HTTP_302_FOUND


# mock_oauth_provider to mock google Oauth user info
def test_callback_google(
    test_client: TestClient, mock_oauth_provider: None, db_session: Session
) -> None:
    response = test_client.get("/v1/auth/callback/google")
    data = response.json()
    assert response.status_code == 200, response.json()
    # check jwt token is generated
    assert data["access_token"] is not None
    assert data["token_type"] == "bearer"
    # check user is created
    payload = jwt.decode(data["access_token"], config.JWT_SECRET_KEY)
    payload.validate()
    user_id = payload.get("sub")
    # get user by id and check user is created

    user = db_session.execute(
        select(sql_models.User).filter(sql_models.User.id == user_id)
    ).scalar_one_or_none()
    assert user is not None
    assert user.auth_provider == MOCK_USER_GOOGLE_AUTH_DATA["iss"]
    assert user.auth_user_id == MOCK_USER_GOOGLE_AUTH_DATA["sub"]
    assert user.email == MOCK_USER_GOOGLE_AUTH_DATA["email"]
    assert user.name == MOCK_USER_GOOGLE_AUTH_DATA["name"]
    assert user.profile_picture == MOCK_USER_GOOGLE_AUTH_DATA["picture"]

    # Clean up: Delete the created user
    db_session.delete(user)
    db_session.commit()


# def test_login_unsupported_provider():
#     response = client.get("/login/unsupported")
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Unsupported provider"}


# def test_callback_unsupported_provider():
#     response = client.get("/callback/unsupported")
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Unsupported provider"}
