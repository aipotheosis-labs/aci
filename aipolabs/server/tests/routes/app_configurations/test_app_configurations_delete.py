from fastapi import status
from fastapi.testclient import TestClient

from aipolabs.common.db.sql_models import App
from aipolabs.common.schemas.app_configurations import AppConfigurationPublic
from aipolabs.server import config


def test_delete_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/"
        f"{dummy_app_configuration_oauth2_google_project_1.app_name}"
    )

    response = test_client.delete(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_200_OK

    # get deleted app configuration should return 404
    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # TODO: check if linked accounts are deleted


def test_delete_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aipolabs_test: App,
) -> None:
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{dummy_app_aipolabs_test.name}",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")
