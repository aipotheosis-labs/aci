from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.integrations import IntegrationPublic

GOOGLE = "GOOGLE"
GITHUB = "GITHUB"
NON_EXISTENT_INTEGRATION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
) -> Generator[list[IntegrationPublic], None, None]:
    """Setup integrations for testing and cleanup after"""
    # add GOOGLE integration
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    google_integration = IntegrationPublic.model_validate(response.json())

    # add GITHUB integration (with different api key)
    payload = {"app_name": GITHUB, "security_scheme": SecurityScheme.API_KEY}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key_2}
    )
    assert response.status_code == 200, response.json()
    github_integration = IntegrationPublic.model_validate(response.json())

    yield [google_integration, github_integration]

    # cleanup
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


# TODO: test updating all other fields
def test_update_integration(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[IntegrationPublic],
) -> None:
    google_integration, _ = setup_and_cleanup

    response = test_client.get(
        f"/v1/integrations/{google_integration.id}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    assert response.json()["enabled"] is True

    response = test_client.patch(
        f"/v1/integrations/{google_integration.id}",
        json={"enabled": False},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["enabled"] is False

    # sanity check by getting the same integration
    response = test_client.get(
        f"/v1/integrations/{google_integration.id}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    assert response.json()["enabled"] is False


def test_update_integration_with_invalid_payload(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[IntegrationPublic],
) -> None:
    google_integration, _ = setup_and_cleanup

    # all_functions_enabled cannot be True when enabled_functions is provided
    response = test_client.patch(
        f"/v1/integrations/{google_integration.id}",
        json={
            "all_functions_enabled": True,
            "enabled_functions": ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        },
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 422, response.json()


def test_update_non_existent_integration(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.patch(
        f"/v1/integrations/{NON_EXISTENT_INTEGRATION_ID}",
        json={"enabled": False},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "Integration not found"


def test_update_integration_with_api_key_of_other_project(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[IntegrationPublic],
) -> None:
    _, github_integration = setup_and_cleanup

    response = test_client.patch(
        f"/v1/integrations/{github_integration.id}",
        json={"enabled": False},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "The integration does not belong to the project"
