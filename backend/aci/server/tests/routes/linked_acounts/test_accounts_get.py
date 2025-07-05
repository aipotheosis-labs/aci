import time
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import LinkedAccount
from aci.common.schemas.linked_accounts import LinkedAccountWithCredentials
from aci.server import config, security_credentials_manager

NON_EXISTENT_LINKED_ACCOUNT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_get_linked_account(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_api_key_2: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
) -> None:
    ENDPOINT_1 = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_1.id}"
    )
    ENDPOINT_2 = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_2.id}"
    )

    response = test_client.get(ENDPOINT_1, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert (
        LinkedAccountWithCredentials.model_validate(response.json()).id
        == dummy_linked_account_oauth2_google_project_1.id
    )

    response = test_client.get(ENDPOINT_2, headers={"x-api-key": dummy_api_key_2})
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert (
        LinkedAccountWithCredentials.model_validate(response.json()).id
        == dummy_linked_account_oauth2_google_project_2.id
    )


def test_get_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{NON_EXISTENT_LINKED_ACCOUNT_ID}"

    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_linked_account_not_belong_to_project(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_2.id}"
    )

    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_linked_account_with_api_key_credentials(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
) -> None:
    """Test that getting a linked account with API key credentials returns only the API key."""
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_api_key_github_project_1.id}"
    )

    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_200_OK

    linked_account = response.json()
    security_credentials = linked_account["security_credentials"]
    assert not security_credentials, "API key credentials should not be exposed for now"


def test_get_linked_account_with_oauth2_credentials(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
) -> None:
    """Test that getting a linked account with OAuth2 credentials returns only the access token."""
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_1.id}"
    )

    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_200_OK

    linked_account = response.json()
    security_credentials: dict[str, str] = linked_account["security_credentials"]
    assert security_credentials["access_token"], "OAuth2 credentials should contain access_token"
    # NOTE: expires_at and refresh_token are optional, but they exist in this mock linked account
    assert security_credentials["expires_at"], "OAuth2 credentials should contain expires_at"
    assert security_credentials["refresh_token"], "OAuth2 credentials should contain refresh_token"


def test_get_linked_account_with_expired_oauth2_credentials(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
) -> None:
    """Test that getting a linked account with expired OAuth2 credentials triggers a refresh."""
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_1.id}"
    )

    # Mock the token refresh response
    mock_refresh_response: dict[str, str | int] = {
        "access_token": "new_mock_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "new_mock_refresh_token",
    }

    # Mock time.time() to return a time after the token has expired
    mock_current_time = int(time.time()) + 7200  # 2 hours in the future

    with (
        patch.object(
            security_credentials_manager,
            "_refresh_oauth2_access_token",
            return_value=mock_refresh_response,
        ) as mock_refresh,
        patch("time.time", return_value=mock_current_time),
    ):
        response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
        assert response.status_code == status.HTTP_200_OK

        linked_account = response.json()
        security_credentials: dict[str, str] = linked_account["security_credentials"]
        assert security_credentials["access_token"] == mock_refresh_response["access_token"]
        assert int(security_credentials["expires_at"]) == (
            mock_current_time + int(mock_refresh_response["expires_in"])
        )
        assert security_credentials["refresh_token"] == mock_refresh_response["refresh_token"]
        mock_refresh.assert_called_once()
