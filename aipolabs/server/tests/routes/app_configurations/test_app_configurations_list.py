from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.app_configurations import AppConfigurationCreate
from aipolabs.server import config

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_google: sql_models.App,
    dummy_app_github: sql_models.App,
) -> Generator[None, None, None]:
    """Setup app configurations for testing and cleanup after"""
    # create google app configuration
    body = AppConfigurationCreate(app_id=dummy_app_google.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()

    # create github app configuration
    body = AppConfigurationCreate(
        app_id=dummy_app_github.id, security_scheme=SecurityScheme.API_KEY
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()

    yield

    # cleanup
    db_session.query(sql_models.AppConfiguration).delete()
    db_session.commit()


def test_list_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/", headers={"x-api-key": dummy_api_key}
    )
    print(response.json())
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 2


def test_list_app_configuration_with_app_id(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_google: sql_models.App,
) -> None:
    # list google app configuration of the project
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/?app_id={dummy_app_google.id}",
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(dummy_app_google.id)


def test_list_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_aipolabs_test: sql_models.App,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/?app_id={dummy_app_aipolabs_test.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 0
