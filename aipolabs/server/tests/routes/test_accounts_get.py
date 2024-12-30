from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.accounts import LinkedAccountPublic
from aipolabs.common.schemas.integrations import IntegrationPublic

GOOGLE = "GOOGLE"
GITHUB = "GITHUB"
NON_EXISTENT_ACCOUNT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
)


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
) -> Generator[list[sql_models.LinkedAccount], None, None]:
    """Setup linked accounts for testing and cleanup after"""
    # create a mock integration for project 1
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    google_integration_1 = IntegrationPublic.model_validate(response.json())

    # create a mock integration for project 2
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key_2}
    )
    assert response.status_code == 200, response.json()
    google_integration_2 = IntegrationPublic.model_validate(response.json())

    # create a mock linked account for project 1
    google_linked_account_1 = crud.create_linked_account(
        db_session,
        google_integration_1.id,
        google_integration_1.project_id,
        google_integration_1.app_id,
        "test_google_account_1",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    # create a mock linked account for project 2
    google_linked_account_2 = crud.create_linked_account(
        db_session,
        google_integration_2.id,
        google_integration_2.project_id,
        google_integration_2.app_id,
        "test_google_account_2",
        SecurityScheme.OAUTH2,
        {"access_token": "mock_access_token"},
        enabled=True,
    )

    db_session.commit()

    yield [google_linked_account_1, google_linked_account_2]

    # cleanup
    db_session.query(sql_models.LinkedAccount).delete()
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


def test_get_linked_account(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    google_linked_account_1, google_linked_account_2 = setup_and_cleanup

    response = test_client.get(
        f"/v1/accounts/{google_linked_account_1.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert LinkedAccountPublic.model_validate(response.json()).id == google_linked_account_1.id

    response = test_client.get(
        f"/v1/accounts/{google_linked_account_2.id}",
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert LinkedAccountPublic.model_validate(response.json()).id == google_linked_account_2.id


def test_get_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"/v1/accounts/{NON_EXISTENT_ACCOUNT_ID}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


def test_get_linked_account_forbidden(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[sql_models.LinkedAccount],
) -> None:
    _, google_linked_account_2 = setup_and_cleanup

    response = test_client.get(
        f"/v1/accounts/{google_linked_account_2.id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
