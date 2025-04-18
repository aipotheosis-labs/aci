from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import App
from aci.common.schemas.app_configurations import AppConfigurationPublic, AppConfigurationsList
from aci.server import config


def test_list_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == str(dummy_app_configuration_oauth2_google_project_1.id)
    assert response.json()[1]["id"] == str(dummy_app_configuration_api_key_github_project_1.id)


def test_list_app_configuration_with_app_id(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_google: App,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
) -> None:
    query_params = AppConfigurationsList(app_names=[dummy_app_google.name])

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        headers={"x-api-key": dummy_api_key_1},
        params=query_params.model_dump(mode="json"),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(dummy_app_configuration_oauth2_google_project_1.id)


def test_list_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aci_test: App,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
) -> None:
    query_params = AppConfigurationsList(app_names=[dummy_app_aci_test.name])

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        headers={"x-api-key": dummy_api_key_1},
        params=query_params.model_dump(mode="json"),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_list_app_configuration_with_limit_and_offset(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
) -> None:
    query_params = AppConfigurationsList(limit=1, offset=0)

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        headers={"x-api-key": dummy_api_key_1},
        # Note: need to exclude None values, otherwise it won't be injected into the query params correctly
        params=query_params.model_dump(exclude_none=True),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
