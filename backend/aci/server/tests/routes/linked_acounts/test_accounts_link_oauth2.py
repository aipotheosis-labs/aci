import time
from typing import cast
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.jose import jwt
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import App
from aci.common.enums import SecurityScheme
from aci.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)
from aci.common.schemas.linked_accounts import (
    LinkedAccountOAuth2Create,
    LinkedAccountOAuth2CreateState,
    LinkedAccountPublic,
)
from aci.common.schemas.security_scheme import (
    OAuth2SchemeCredentials,
    OAuth2SchemeOverride,
    SecuritySchemeOverrides,
)
from aci.server import config

MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
)


@pytest.mark.parametrize(
    "use_custom_oauth2_app,after_oauth2_link_redirect_url,callback_response_code",
    [
        (False, None, status.HTTP_200_OK),
        (False, "https://platform.aci.dev", status.HTTP_302_FOUND),
        (True, None, status.HTTP_200_OK),
        (True, "https://platform.aci.dev", status.HTTP_302_FOUND),
    ],
)
def test_link_oauth2_account_success(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_google: App,
    db_session: Session,
    use_custom_oauth2_app: bool,
    after_oauth2_link_redirect_url: str | None,
    callback_response_code: int,
) -> None:
    # create a new app configuration
    if use_custom_oauth2_app:
        app_configuration_create = AppConfigurationCreate(
            app_name=dummy_app_google.name,
            security_scheme=SecurityScheme.OAUTH2,
            security_scheme_overrides=SecuritySchemeOverrides(
                oauth2=OAuth2SchemeOverride(
                    client_id="custom_client_id",
                    client_secret="custom_client_secret",
                )
            ),
        )
    else:
        app_configuration_create = AppConfigurationCreate(
            app_name=dummy_app_google.name,
            security_scheme=SecurityScheme.OAUTH2,
        )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=app_configuration_create.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    google_app_configuration = AppConfigurationPublic.model_validate(response.json())

    # init account linking proces
    body = LinkedAccountOAuth2Create(
        app_name=dummy_app_google.name,
        linked_account_owner_id="test_link_oauth2_account_success",
        after_oauth2_link_redirect_url=after_oauth2_link_redirect_url,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2",
        params=body.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    authorization_url = str(response.json()["url"])
    assert authorization_url.startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    qs_params = parse_qs(urlparse(authorization_url).query)
    state_jwt = qs_params.get("state", [None])[0]
    assert state_jwt is not None
    state = LinkedAccountOAuth2CreateState.model_validate(jwt.decode(state_jwt, config.SIGNING_KEY))
    assert state.project_id == google_app_configuration.project_id
    assert state.app_name == google_app_configuration.app_name
    assert state.linked_account_owner_id == "test_link_oauth2_account_success"
    assert state.after_oauth2_link_redirect_url == after_oauth2_link_redirect_url
    assert state.redirect_uri == (
        f"{config.REDIRECT_URI_BASE}{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2/callback"
    )
    if use_custom_oauth2_app:
        assert state.client_id == "custom_client_id"
    else:
        assert (
            state.client_id == dummy_app_google.security_schemes[SecurityScheme.OAUTH2]["client_id"]
        )

    # mock the oauth2 manager's fetch_token response
    mock_oauth2_token_response = {
        "access_token": "mock_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "mock_refresh_token",
    }

    # Mock time.time() to return a consistent value
    mock_oauth2_token_retrieval_time = int(time.time())
    with (
        patch(
            "aci.server.oauth2_manager.OAuth2Manager.fetch_token",
            new=AsyncMock(return_value=mock_oauth2_token_response),
        ),
        patch("time.time", return_value=mock_oauth2_token_retrieval_time),
    ):
        # simulate the OAuth2 provider calling back with 'state' & 'code'
        callback_params = {
            "state": state_jwt,
            # in real world, this is provided by provider, but we just mock it
            "code": "mock_auth_code",
        }
        response = test_client.get(
            f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2/callback",
            params=callback_params,
        )
        assert response.status_code == callback_response_code

        # check linked account is created with the correct values
        linked_account = crud.linked_accounts.get_linked_account(
            db_session,
            state.project_id,
            state.app_name,
            state.linked_account_owner_id,
        )
        assert linked_account is not None
        oauth2_credentials = OAuth2SchemeCredentials.model_validate(
            linked_account.security_credentials
        )
        assert linked_account.security_scheme == SecurityScheme.OAUTH2
        assert (
            oauth2_credentials.scope
            == dummy_app_google.security_schemes[SecurityScheme.OAUTH2]["scope"]
        )
        assert oauth2_credentials.access_token == mock_oauth2_token_response["access_token"]
        assert oauth2_credentials.token_type == mock_oauth2_token_response["token_type"]
        assert oauth2_credentials.expires_at == mock_oauth2_token_retrieval_time + cast(
            int, mock_oauth2_token_response["expires_in"]
        )
        assert oauth2_credentials.refresh_token == mock_oauth2_token_response["refresh_token"]
        assert oauth2_credentials.raw_token_response == mock_oauth2_token_response
        assert linked_account.enabled is True
        assert linked_account.app.name == google_app_configuration.app_name
        assert linked_account.project_id == google_app_configuration.project_id
        assert linked_account.linked_account_owner_id == state.linked_account_owner_id

        if use_custom_oauth2_app:
            assert oauth2_credentials.client_id == "custom_client_id"
            assert oauth2_credentials.client_secret == "custom_client_secret"
        else:
            assert (
                oauth2_credentials.client_id
                == dummy_app_google.security_schemes[SecurityScheme.OAUTH2]["client_id"]
            )
            assert (
                oauth2_credentials.client_secret
                == dummy_app_google.security_schemes[SecurityScheme.OAUTH2]["client_secret"]
            )

        if not after_oauth2_link_redirect_url:
            assert LinkedAccountPublic.model_validate(response.json()), (
                "should return linked account in response if after_oauth2_link_redirect_url is not provided"
            )


def test_link_oauth2_account_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aci_test: App,
) -> None:
    body = LinkedAccountOAuth2Create(
        app_name=dummy_app_aci_test.name,
        linked_account_owner_id="test_link_oauth2_account_non_existent_app_configuration",
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2",
        params=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")


@pytest.mark.parametrize(
    "redirect_url", [None, "https://api.user-app.com/v1/linked-accounts/oauth2/callback"]
)
def test_link_oauth2_account_under_app_config_with_custom_redirect_url(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_google: App,
    redirect_url: str | None,
) -> None:
    # create app configuration
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_google.name,
        security_scheme=SecurityScheme.OAUTH2,
        security_scheme_overrides=SecuritySchemeOverrides(
            oauth2=OAuth2SchemeOverride(
                client_id="custom_client_id",
                client_secret="custom_client_secret",
                redirect_url=redirect_url,
            )
        ),
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=app_configuration_create.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK

    # get oauth2 account linking URL
    linked_account_oauth2_create = LinkedAccountOAuth2Create(
        app_name=dummy_app_google.name,
        linked_account_owner_id="test_link_oauth2_account_with_custom_redirect_url",
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2",
        params=linked_account_oauth2_create.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    authorization_url = str(response.json()["url"])
    assert authorization_url.startswith(MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX)
    qs_params = parse_qs(urlparse(authorization_url).query)

    # validate redirect_uri in authorization url and state are correct
    redirect_uri_in_authorization_url = qs_params.get("redirect_uri", [None])[0]
    state_jwt = qs_params.get("state", [None])[0]
    assert redirect_uri_in_authorization_url is not None
    assert state_jwt is not None
    state = LinkedAccountOAuth2CreateState.model_validate(jwt.decode(state_jwt, config.SIGNING_KEY))

    if redirect_url:
        assert redirect_uri_in_authorization_url == redirect_url
        assert state.redirect_uri == redirect_url
    else:
        assert (
            redirect_uri_in_authorization_url
            == f"{config.REDIRECT_URI_BASE}{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2/callback"
        )
        assert (
            state.redirect_uri
            == f"{config.REDIRECT_URI_BASE}{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2/callback"
        )
