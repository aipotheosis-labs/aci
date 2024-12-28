from datetime import datetime, timezone
from typing import Generator
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.jose import jwt
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.server import config

GOOGLE = "GOOGLE"
GITHUB = "GITHUB"
NON_EXISTENT_INTEGRATION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
)


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
) -> Generator[tuple[str, str], None, None]:
    """Setup integrations for testing and cleanup after"""
    # add GOOGLE integration
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    google_integration_id = response.json()["integration_id"]

    # add GITHUB integration (with different api key)
    payload = {"app_name": GITHUB, "security_scheme": SecurityScheme.API_KEY}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key_2}
    )
    assert response.status_code == 200, response.json()
    github_integration_id = response.json()["integration_id"]

    yield google_integration_id, github_integration_id

    # cleanup
    db_session.query(sql_models.ProjectAppIntegration).delete()
    db_session.commit()


# @pytest.fixture
# def mock_oauth_provider(monkeypatch: pytest.MonkeyPatch) -> None:
#     class MockOAuthClient:
#         async def authorize_access_token(self, request: Request) -> dict[str, dict]:
#             return {"userinfo": MOCK_USER_GOOGLE_AUTH_DATA}

#     # Mock the OAuth client creation
#     def mock_create_client(provider: str) -> MockOAuthClient:
#         return MockOAuthClient()

#     # Mock the OAuth provider registry
#     monkeypatch.setattr(
#         "aipolabs.server.routes.auth.oauth._registry", {"google": "mock_google_client"}
#     )
#     monkeypatch.setattr("aipolabs.server.routes.auth.oauth.create_client", mock_create_client)


def test_link_oauth2_account_success(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: Generator[tuple[str, str], None, None],
) -> None:
    google_integration_id, _ = setup_and_cleanup

    # step 1: init account linking process
    response = test_client.post(
        "/v1/accounts/",
        json={
            "integration_id": google_integration_id,
            "account_name": "test_account",
        },
        headers={"x-api-key": dummy_api_key},
    )

    # This is a redirect response, but we are not following the redirect
    # (follow_redirects=False was set when creating the test client)
    assert response.status_code == status.HTTP_302_FOUND
    redirect_location = response.headers["location"]
    assert redirect_location.startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    qs_params = parse_qs(urlparse(redirect_location).query)
    state_jwt = qs_params.get("state", [None])[0]
    assert state_jwt is not None
    state = jwt.decode(state_jwt, config.JWT_SECRET_KEY)
    assert state["integration_id"] == google_integration_id
    assert state["account_name"] == "test_account"
    assert state["iat"] > int(datetime.now(timezone.utc).timestamp()) - 3, "iat should be recent"
    assert state["nonce"] is not None

    # step 2: simulate the OAuth2 provider calling back your endpoint with 'state' & 'code'
    callback_params = {
        "state": state_jwt,
        "code": "mock_auth_code",  # Usually provided by provider, but we just mock it
    }
    response = test_client.get("/v1/accounts/oauth2/callback", params=callback_params)
    assert response.status_code == 200, response.json()


# # mock_oauth_provider to mock google Oauth user info
# def test_callback_google(
#     test_client: TestClient, mock_oauth_provider: None, db_session: Session
# ) -> None:
#     response = test_client.get("/v1/auth/callback/google")
#     data = response.json()
#     assert response.status_code == 200, response.json()
#     # check jwt token is generated
#     assert data["access_token"] is not None
#     assert data["token_type"] == "bearer"
#     # check user is created
#     payload = jwt.decode(data["access_token"], config.JWT_SECRET_KEY)
#     payload.validate()
#     user_id = payload.get("sub")
#     # get user by id and check user is created

#     user = db_session.execute(
#         select(sql_models.User).filter(sql_models.User.id == user_id)
#     ).scalar_one_or_none()
#     assert user is not None

#     # Clean up: Delete the created user
#     db_session.delete(user)
#     db_session.commit()
