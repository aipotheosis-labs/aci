from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.integrations import IntegrationCreate, IntegrationPublic

NON_EXISTENT_INTEGRATION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[sql_models.App],
) -> Generator[list[sql_models.LinkedAccount], None, None]:
    """Setup linked accounts for testing and cleanup after"""
    dummy_app_1 = dummy_apps[0]
    dummy_app_2 = dummy_apps[1]
    # add integration
    body = IntegrationCreate(
        app_id=dummy_app_1.id,
        security_scheme=SecurityScheme.OAUTH2,
    )
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    dummy_app_1_integration = IntegrationPublic.model_validate(response.json())

    # add integration
    body = IntegrationCreate(
        app_id=dummy_app_2.id,
        security_scheme=SecurityScheme.OAUTH2,
    )
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    dummy_app_2_integration = IntegrationPublic.model_validate(response.json())

    # create mock linked accounts
    dummy_app_1_linked_account_1 = crud.create_linked_account(
        db_session,
        dummy_app_1_integration.id,
        dummy_app_1_integration.project_id,
        dummy_app_1_integration.app_id,
        "test_dummy_app_1_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    dummy_app_1_linked_account_2 = crud.create_linked_account(
        db_session,
        dummy_app_1_integration.id,
        dummy_app_1_integration.project_id,
        dummy_app_1_integration.app_id,
        "test_dummy_app_1_account_2",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    dummy_app_2_linked_account_1 = crud.create_linked_account(
        db_session,
        dummy_app_2_integration.id,
        dummy_app_2_integration.project_id,
        dummy_app_2_integration.app_id,
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
    db_session.query(sql_models.LinkedAccount).delete()
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


def test_list_linked_accounts_no_filters(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 3


def test_list_linked_accounts_filter_by_app_id(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    dummy_app_2_linked_account_1 = setup_and_cleanup[2]

    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id": str(dummy_app_2_linked_account_1.app_id)},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(dummy_app_2_linked_account_1.app_id)
    assert response.json()[0]["account_name"] == dummy_app_2_linked_account_1.account_name


def test_list_linked_accounts_filter_by_account_name(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    github_linked_account = setup_and_cleanup[2]

    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={"account_name": github_linked_account.account_name},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(github_linked_account.app_id)
    assert response.json()[0]["account_name"] == github_linked_account.account_name


def test_list_linked_accounts_filter_by_app_id_and_account_name(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    dummy_app_1_linked_account_1 = setup_and_cleanup[0]

    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={
            "app_id": str(dummy_app_1_linked_account_1.app_id),
            "account_name": dummy_app_1_linked_account_1.account_name,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(dummy_app_1_linked_account_1.app_id)
    assert response.json()[0]["account_name"] == dummy_app_1_linked_account_1.account_name


def test_list_linked_accounts_filter_by_non_existent_app_id(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id": NON_EXISTENT_INTEGRATION_ID},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 0
