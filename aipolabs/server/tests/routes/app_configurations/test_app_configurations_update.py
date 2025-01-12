from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import App, AppConfiguration
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)
from aipolabs.server import config


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
    dummy_app_google: App,
    dummy_app_github: App,
) -> Generator[list[AppConfigurationPublic], None, None]:
    """Setup app configurations for testing and cleanup after"""
    # create google app configuration
    body = AppConfigurationCreate(app_id=dummy_app_google.id, security_scheme=SecurityScheme.OAUTH2)

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    google_app_configuration = AppConfigurationPublic.model_validate(response.json())

    # create github app configuration under different project (with different api key)
    body = AppConfigurationCreate(
        app_id=dummy_app_github.id, security_scheme=SecurityScheme.API_KEY
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == status.HTTP_200_OK
    github_app_configuration = AppConfigurationPublic.model_validate(response.json())

    yield [google_app_configuration, github_app_configuration]

    # cleanup
    db_session.query(AppConfiguration).delete()
    db_session.commit()


# TODO: test updating all other fields
def test_update_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[AppConfigurationPublic],
) -> None:
    google_app_configuration, _ = setup_and_cleanup

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{google_app_configuration.app_id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] is True

    response = test_client.patch(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{google_app_configuration.app_id}",
        json={"enabled": False},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] is False

    # sanity check by getting the same app configuration
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{google_app_configuration.app_id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] is False


def test_update_app_configuration_with_invalid_payload(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[AppConfigurationPublic],
) -> None:
    google_app_configuration, _ = setup_and_cleanup

    # all_functions_enabled cannot be True when enabled_functions is provided
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{google_app_configuration.app_id}",
        json={
            "all_functions_enabled": True,
            "enabled_functions": ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        },
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_aipolabs_test: App,
) -> None:
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{dummy_app_aipolabs_test.id}",
        json={"enabled": False},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")
