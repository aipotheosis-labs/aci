from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, AppConfiguration, LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)
from aipolabs.common.schemas.linked_accounts import LinkedAccountPublic
from aipolabs.server import config

NON_EXISTENT_ACCOUNT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
    dummy_apps: list[App],
) -> Generator[list[LinkedAccount], None, None]:
    """Setup linked accounts for testing and cleanup after"""
    dummy_app_1 = dummy_apps[0]
    dummy_app_2 = dummy_apps[1]
    # create a mock app configuration for project 1
    body = AppConfigurationCreate(
        app_id=dummy_app_1.id,
        security_scheme=SecurityScheme.OAUTH2,
        security_config_overrides={},
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    app_configuration_1 = AppConfigurationPublic.model_validate(response.json())

    # create a mock app configuration for project 2
    body = AppConfigurationCreate(
        app_id=dummy_app_2.id,
        security_scheme=SecurityScheme.OAUTH2,
        security_config_overrides={},
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == 200, response.json()
    app_configuration_2 = AppConfigurationPublic.model_validate(response.json())

    # create a mock linked account for project 1
    linked_account_1 = crud.linked_accounts.create_linked_account(
        db_session,
        app_configuration_1.project_id,
        app_configuration_1.app_id,
        "test_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    # create a mock linked account for project 2
    linked_account_2 = crud.linked_accounts.create_linked_account(
        db_session,
        app_configuration_2.project_id,
        app_configuration_2.app_id,
        "test_account_2",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    db_session.commit()

    yield [linked_account_1, linked_account_2]

    # cleanup
    db_session.query(LinkedAccount).delete()
    db_session.query(AppConfiguration).delete()
    db_session.commit()


def test_get_linked_account(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
    setup_and_cleanup: list[LinkedAccount],
) -> None:
    linked_account_1, linked_account_2 = setup_and_cleanup

    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{linked_account_1.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert LinkedAccountPublic.model_validate(response.json()).id == linked_account_1.id

    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{linked_account_2.id}",
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert LinkedAccountPublic.model_validate(response.json()).id == linked_account_2.id


def test_get_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{NON_EXISTENT_ACCOUNT_ID}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


def test_get_linked_account_forbidden(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[LinkedAccount],
) -> None:
    _, linked_account_2 = setup_and_cleanup

    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{linked_account_2.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
