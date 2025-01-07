from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)

NON_EXISTENT_ACCOUNT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
    dummy_apps: list[sql_models.App],
) -> Generator[list[sql_models.LinkedAccount], None, None]:
    """Setup linked accounts for testing and cleanup after"""
    dummy_app_1 = dummy_apps[0]
    # create a app configuration for project 1
    body = AppConfigurationCreate(
        app_id=dummy_app_1.id,
        security_scheme=SecurityScheme.OAUTH2,
    )
    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    app_configuration_1 = AppConfigurationPublic.model_validate(response.json())

    # create a mock app configuration for project 2
    body = AppConfigurationCreate(
        app_id=dummy_app_1.id,
        security_scheme=SecurityScheme.OAUTH2,
    )
    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == 200, response.json()
    app_configuration_2 = AppConfigurationPublic.model_validate(response.json())

    # create a mock linked account for app_configuration_1
    linked_account_1 = crud.create_linked_account(
        db_session,
        app_configuration_1.project_id,
        app_configuration_1.app_id,
        "test_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    # create a mock linked account for app_configuration_2
    linked_account_2 = crud.create_linked_account(
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
    db_session.query(sql_models.LinkedAccount).delete()
    db_session.query(sql_models.AppConfiguration).delete()
    db_session.commit()


def test_delete_linked_account(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    linked_account_1, _ = setup_and_cleanup

    response = test_client.delete(
        f"/v1/linked-accounts/{linked_account_1.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()

    # check that the linked account was deleted
    response = test_client.get(
        f"/v1/linked-accounts/{linked_account_1.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


def test_delete_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.delete(
        f"/v1/linked-accounts/{NON_EXISTENT_ACCOUNT_ID}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


def test_delete_linked_account_forbidden(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    _, linked_account_2 = setup_and_cleanup

    response = test_client.delete(
        f"/v1/linked-accounts/{linked_account_2.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
