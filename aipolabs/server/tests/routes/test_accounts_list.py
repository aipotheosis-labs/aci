from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.integrations import IntegrationPublic

GOOGLE = "GOOGLE"
GITHUB = "GITHUB"
NON_EXISTENT_INTEGRATION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
)


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
) -> Generator[list[sql_models.LinkedAccount], None, None]:
    """Setup linked accounts for testing and cleanup after"""
    # add GOOGLE integrations
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    google_integration = IntegrationPublic.model_validate(response.json())

    # add GITHUB integration
    payload = {"app_name": GITHUB, "security_scheme": SecurityScheme.OAUTH2}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    github_integration = IntegrationPublic.model_validate(response.json())

    # create mock linked accounts
    google_linked_account_1 = crud.create_linked_account(
        db_session,
        google_integration.id,
        google_integration.project_id,
        google_integration.app_id,
        "test_google_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    google_linked_account_2 = crud.create_linked_account(
        db_session,
        google_integration.id,
        google_integration.project_id,
        google_integration.app_id,
        "test_google_account_2",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    github_linked_account = crud.create_linked_account(
        db_session,
        github_integration.id,
        github_integration.project_id,
        github_integration.app_id,
        "test_github_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )
    db_session.commit()

    yield [google_linked_account_1, google_linked_account_2, github_linked_account]

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
    github_linked_account = setup_and_cleanup[2]

    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id_or_name": str(github_linked_account.app_id)},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(github_linked_account.app_id)
    assert response.json()[0]["account_name"] == github_linked_account.account_name


def test_list_linked_accounts_filter_by_app_name(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    github_linked_account = setup_and_cleanup[2]

    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id_or_name": GITHUB},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(github_linked_account.app_id)
    assert response.json()[0]["account_name"] == github_linked_account.account_name


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
    google_linked_account_1 = setup_and_cleanup[0]

    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id_or_name": GOOGLE, "account_name": google_linked_account_1.account_name},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(google_linked_account_1.app_id)
    assert response.json()[0]["account_name"] == google_linked_account_1.account_name


def test_list_linked_accounts_filter_by_non_existent_app_name(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        "/v1/accounts/",
        headers={"x-api-key": dummy_api_key},
        params={"app_id_or_name": "non_existent_app_name"},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 0
