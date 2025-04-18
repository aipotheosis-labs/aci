from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import App
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.server import config


# TODO: test updating all other fields
def test_update_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/"
        f"{dummy_app_configuration_oauth2_google_project_1.app_name}"
    )

    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] is True

    response = test_client.patch(
        ENDPOINT, json={"enabled": False}, headers={"x-api-key": dummy_api_key_1}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] is False

    # sanity check by getting the same app configuration
    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] is False


def test_update_app_configuration_with_invalid_payload(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/"
        f"{dummy_app_configuration_oauth2_google_project_1.app_name}"
    )

    # all_functions_enabled cannot be True when enabled_functions is provided
    response = test_client.patch(
        ENDPOINT,
        json={
            "all_functions_enabled": True,
            "enabled_functions": ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        },
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aci_test: App,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{dummy_app_aci_test.name}"

    response = test_client.patch(
        ENDPOINT,
        json={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")
