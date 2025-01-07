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
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)
from aipolabs.common.schemas.linked_accounts import LinkedAccountCreate
from aipolabs.server import config
from aipolabs.server.routes.linked_accounts import LinkedAccountCreateOAuth2State

MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
)


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
    dummy_app_google: sql_models.App,
    dummy_app_github: sql_models.App,
) -> Generator[list[AppConfigurationPublic], None, None]:
    """Setup app configurations for testing and cleanup after"""
    # create google app configuration
    body = AppConfigurationCreate(
        app_id=dummy_app_google.id,
        security_scheme=SecurityScheme.OAUTH2,
        security_config_overrides={},
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    google_app_configuration = AppConfigurationPublic.model_validate(response.json())

    # create github app configuration under different project (with different api key)
    body = AppConfigurationCreate(
        app_id=dummy_app_github.id,
        security_scheme=SecurityScheme.API_KEY,
        security_config_overrides={},
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == 200, response.json()
    github_app_configuration = AppConfigurationPublic.model_validate(response.json())

    yield [google_app_configuration, github_app_configuration]

    # cleanup
    db_session.query(sql_models.AppConfiguration).delete()
    db_session.commit()


def test_link_oauth2_account_success(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[AppConfigurationPublic],
    db_session: Session,
) -> None:
    google_app_configuration, _ = setup_and_cleanup

    # init account linking proces, trigger redirect to oauth2 provider
    body = LinkedAccountCreate(
        app_id=google_app_configuration.app_id,
        linked_account_owner_id="test_account",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/",
        json=body.model_dump(mode="json"),
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
    state = LinkedAccountCreateOAuth2State.model_validate(
        jwt.decode(state_jwt, config.JWT_SECRET_KEY)
    )
    assert state.app_id == google_app_configuration.app_id
    assert state.linked_account_owner_id == "test_account"
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
        response = test_client.get(
            f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2/callback", params=callback_params
        )
        assert response.status_code == 200, response.json()

    # check linked account is created with the correct values
    linked_account = crud.get_linked_account(
        db_session,
        state.project_id,
        state.app_id,
        state.linked_account_owner_id,
    )
    assert linked_account is not None
    assert linked_account.security_scheme == SecurityScheme.OAUTH2
    assert linked_account.security_credentials == mock_oauth2_token_response
    assert linked_account.enabled is True
    assert linked_account.app_id == google_app_configuration.app_id
    assert linked_account.project_id == state.project_id
    assert linked_account.app_id == state.app_id
    assert linked_account.linked_account_owner_id == state.linked_account_owner_id

    # cleanup
    crud.delete_linked_account(db_session, linked_account.id)
    db_session.commit()


def test_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_aipolabs_test: sql_models.App,
) -> None:
    body = LinkedAccountCreate(
        app_id=dummy_app_aipolabs_test.id,
        linked_account_owner_id="test_account",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()
    assert response.json()["detail"] == "App not configured"
