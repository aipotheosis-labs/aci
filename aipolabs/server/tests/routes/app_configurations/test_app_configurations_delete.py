from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
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
    dummy_app_google: sql_models.App,
    dummy_app_github: sql_models.App,
) -> Generator[list[AppConfigurationPublic], None, None]:
    """Setup app configurations for testing and cleanup after"""
    # create google app configuration
    body = AppConfigurationCreate(app_id=dummy_app_google.id, security_scheme=SecurityScheme.OAUTH2)

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    google_app_configuration = AppConfigurationPublic.model_validate(response.json())

    # create github app configuration
    body = AppConfigurationCreate(
        app_id=dummy_app_github.id, security_scheme=SecurityScheme.API_KEY
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


def test_delete_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[AppConfigurationPublic],
) -> None:
    google_app_configuration, _ = setup_and_cleanup

    response = test_client.delete(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{google_app_configuration.app_id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()

    # get deleted app configuration should return 404
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{google_app_configuration.app_id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 404, response.json()
    # TODO: check if linked accounts are deleted


def test_delete_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_aipolabs_test: sql_models.App,
) -> None:
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{dummy_app_aipolabs_test.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "App configuration not found"
