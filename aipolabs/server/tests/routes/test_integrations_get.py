from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.integrations import IntegrationCreate, IntegrationPublic

NON_EXISTENT_INTEGRATION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_api_key_2: str,
    dummy_google_app: sql_models.App,
    dummy_github_app: sql_models.App,
) -> Generator[list[IntegrationPublic], None, None]:
    """Setup integrations for testing and cleanup after"""
    # add google integration
    body = IntegrationCreate(app_id=dummy_google_app.id, security_scheme=SecurityScheme.OAUTH2)

    response = test_client.post(
        "/v1/integrations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    google_integration = IntegrationPublic.model_validate(response.json())

    # add github integration (with different api key)
    body = IntegrationCreate(app_id=dummy_github_app.id, security_scheme=SecurityScheme.API_KEY)

    response = test_client.post(
        "/v1/integrations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == 200, response.json()
    github_integration = IntegrationPublic.model_validate(response.json())

    yield [google_integration, github_integration]

    # cleanup
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


def test_get_integration(
    test_client: TestClient,
    dummy_api_key: str,
    setup_and_cleanup: list[IntegrationPublic],
) -> None:
    google_integration, _ = setup_and_cleanup

    response = test_client.get(
        f"/v1/integrations/{google_integration.id}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    integration = IntegrationPublic.model_validate(response.json())
    assert integration.id == google_integration.id


def test_get_integration_with_non_existent_integration(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"/v1/integrations/{NON_EXISTENT_INTEGRATION_ID}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "Integration not found"


def test_get_integration_with_api_key_of_other_project(
    test_client: TestClient,
    dummy_api_key_2: str,
    setup_and_cleanup: list[IntegrationPublic],
) -> None:
    google_integration, _ = setup_and_cleanup

    response = test_client.get(
        f"/v1/integrations/{google_integration.id}", headers={"x-api-key": dummy_api_key_2}
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "The integration does not belong to the project"
