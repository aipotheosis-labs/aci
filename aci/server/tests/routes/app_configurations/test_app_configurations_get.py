from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import App
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.server import config


def test_get_app_configuration(
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
    app_configuration = AppConfigurationPublic.model_validate(response.json())
    assert app_configuration.id == dummy_app_configuration_oauth2_google_project_1.id


def test_get_app_configuration_with_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aci_test: App,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{dummy_app_aci_test.name}"
    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")
