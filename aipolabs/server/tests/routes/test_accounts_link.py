from datetime import datetime, timezone
from typing import Generator
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.integrations.starlette_client import StarletteOAuth2App
from authlib.jose import jwt
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.integrations import IntegrationPublic
from aipolabs.server import config
from aipolabs.server.routes.accounts import AccountCreateOAuth2State

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
) -> Generator[list[IntegrationPublic], None, None]:
    """Setup integrations for testing and cleanup after"""
    # add GOOGLE integration
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    google_integration = IntegrationPublic.model_validate(response.json())

    # add GITHUB integration (with different api key)
    payload = {"app_name": GITHUB, "security_scheme": SecurityScheme.API_KEY}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key_2}
    )
    assert response.status_code == 200, response.json()
    github_integration = IntegrationPublic.model_validate(response.json())

    yield [google_integration, github_integration]

    # cleanup
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


def test_link_oauth2_account_success(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[IntegrationPublic],
    db_session: Session,
) -> None:
    google_integration, _ = setup_and_cleanup

    # init account linking proces, trigger redirect to oauth2 provider
    response = test_client.post(
        "/v1/accounts/",
        json={
            "integration_id": str(google_integration.id),
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
    state = AccountCreateOAuth2State.model_validate(jwt.decode(state_jwt, config.JWT_SECRET_KEY))
    assert state.integration_id == google_integration.id
    assert state.account_name == "test_account"
    assert state.iat > int(datetime.now(timezone.utc).timestamp()) - 3, "iat should be recent"
    assert state.nonce is not None

    # mock the oauth2 client's authorize_access_token method
    mock_oauth2_token_response = {
        "access_token": "mock_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "mock_scope",
        "refresh_token": "mock_refresh_token",
    }
    with patch.object(
        StarletteOAuth2App,
        "authorize_access_token",
        return_value=mock_oauth2_token_response,
    ):
        # simulate the OAuth2 provider calling back with 'state' & 'code'
        callback_params = {
            "state": state_jwt,
            "code": "mock_auth_code",  # Usually provided by provider, but we just mock it
        }
        response = test_client.get("/v1/accounts/oauth2/callback", params=callback_params)
        assert response.status_code == 200, response.json()

    # check linked account is created with the correct values
    linked_account = crud.get_linked_account(
        db_session,
        state.project_id,
        state.app_id,
        state.account_name,
    )
    assert linked_account is not None
    assert linked_account.security_scheme == SecurityScheme.OAUTH2
    assert linked_account.security_credentials == mock_oauth2_token_response
    assert linked_account.enabled is True
    assert linked_account.integration_id == google_integration.id
    assert linked_account.project_id == state.project_id
    assert linked_account.app_id == state.app_id
    assert linked_account.account_name == state.account_name

    # cleanup
    crud.delete_linked_account(db_session, linked_account.id)
    db_session.commit()


def test_non_existent_integration_id(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.post(
        "/v1/accounts/",
        json={"integration_id": NON_EXISTENT_INTEGRATION_ID, "account_name": "test_account"},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()
    assert response.json()["detail"] == "Integration not found"


def test_integration_not_belong_to_project(
    test_client: TestClient,
    dummy_api_key_2: str,
    setup_and_cleanup: list[IntegrationPublic],
) -> None:
    google_integration, _ = setup_and_cleanup

    response = test_client.post(
        "/v1/accounts/",
        json={"integration_id": str(google_integration.id), "account_name": "test_account"},
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
    assert response.json()["detail"] == "The integration does not belong to the project"
