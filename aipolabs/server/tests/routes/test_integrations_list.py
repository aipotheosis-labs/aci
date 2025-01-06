from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.schemas.integrations import IntegrationCreate

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True, scope="module")
def setup_and_cleanup(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
    dummy_google_app: sql_models.App,
    dummy_github_app: sql_models.App,
) -> Generator[None, None, None]:
    """Setup integrations for testing and cleanup after"""
    # add google integration
    body = IntegrationCreate(app_id=dummy_google_app.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()

    # add github integration
    body = IntegrationCreate(app_id=dummy_github_app.id, security_scheme=SecurityScheme.API_KEY)

    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()

    yield

    # cleanup
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


def test_list_integration(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get("/v1/integrations/", headers={"x-api-key": dummy_api_key})
    print(response.json())
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 2


def test_list_integration_with_app_id(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[sql_models.App],
    dummy_google_app: sql_models.App,
) -> None:
    # list google app integration of the project
    response = test_client.get(
        f"/v1/integrations/?app_id={dummy_google_app.id}", headers={"x-api-key": dummy_api_key}
    )

    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(dummy_google_app.id)


def test_list_integration_with_non_existent_app_id(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"/v1/integrations/?app_id={NON_EXISTENT_APP_ID}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 0
