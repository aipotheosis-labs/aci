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
from aipolabs.server import config


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[App],
) -> Generator[list[LinkedAccount], None, None]:
    """Setup linked accounts for testing and cleanup after"""
    dummy_app_1 = dummy_apps[0]
    dummy_app_2 = dummy_apps[1]
    # create app configuration
    body = AppConfigurationCreate(
        app_id=dummy_app_1.id,
        security_scheme=SecurityScheme.OAUTH2,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    dummy_app_1_app_configuration = AppConfigurationPublic.model_validate(response.json())

    # create app configuration
    body = AppConfigurationCreate(
        app_id=dummy_app_2.id,
        security_scheme=SecurityScheme.OAUTH2,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    dummy_app_2_app_configuration = AppConfigurationPublic.model_validate(response.json())

    # create mock linked accounts
    dummy_app_1_linked_account_1 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_1_app_configuration.project_id,
        dummy_app_1_app_configuration.app_id,
        "test_dummy_app_1_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    dummy_app_1_linked_account_2 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_1_app_configuration.project_id,
        dummy_app_1_app_configuration.app_id,
        "test_dummy_app_1_account_2",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    dummy_app_2_linked_account_1 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_2_app_configuration.project_id,
        dummy_app_2_app_configuration.app_id,
        "test_dummy_app_2_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )
    db_session.commit()

    yield [
        dummy_app_1_linked_account_1,
        dummy_app_1_linked_account_2,
        dummy_app_2_linked_account_1,
    ]

    # cleanup
    db_session.query(LinkedAccount).delete()
    db_session.query(AppConfiguration).delete()
    db_session.commit()


def test_list_linked_accounts_no_filters(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 3


def test_list_linked_accounts_filter_by_app_id(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[LinkedAccount],
) -> None:
    dummy_app_2_linked_account_1 = setup_and_cleanup[2]

    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id": str(dummy_app_2_linked_account_1.app_id)},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(dummy_app_2_linked_account_1.app_id)
    assert (
        response.json()[0]["linked_account_owner_id"]
        == dummy_app_2_linked_account_1.linked_account_owner_id
    )


def test_list_linked_accounts_filter_by_account_name(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[LinkedAccount],
) -> None:
    github_linked_account = setup_and_cleanup[2]

    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/",
        headers={"x-api-key": dummy_api_key},
        params={"linked_account_owner_id": github_linked_account.linked_account_owner_id},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(github_linked_account.app_id)
    assert (
        response.json()[0]["linked_account_owner_id"]
        == github_linked_account.linked_account_owner_id
    )


def test_list_linked_accounts_filter_by_app_id_and_account_name(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[LinkedAccount],
) -> None:
    dummy_app_1_linked_account_1 = setup_and_cleanup[0]

    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/",
        headers={"x-api-key": dummy_api_key},
        params={
            "app_id": str(dummy_app_1_linked_account_1.app_id),
            "linked_account_owner_id": dummy_app_1_linked_account_1.linked_account_owner_id,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(dummy_app_1_linked_account_1.app_id)
    assert (
        response.json()[0]["linked_account_owner_id"]
        == dummy_app_1_linked_account_1.linked_account_owner_id
    )


def test_list_linked_accounts_filter_by_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_aipolabs_test: App,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id": str(dummy_app_aipolabs_test.id)},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 0
