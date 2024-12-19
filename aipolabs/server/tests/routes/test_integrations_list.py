from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import sql_models
from aipolabs.common.enums import SecurityScheme

GOOGLE = "GOOGLE"
GITHUB = "GITHUB"
NON_EXISTENT_APP = "NON_EXISTENT_APP"


@pytest.fixture(autouse=True, scope="module")
def cleanup_integrations(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key: str,
) -> Generator[None, None, None]:
    """Setup integrations for testing and cleanup after"""
    # add GOOGLE integration
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()

    # add GITHUB integration
    payload = {"app_name": GITHUB, "security_scheme": SecurityScheme.API_KEY}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()

    yield

    # cleanup
    db_session.query(sql_models.ProjectAppIntegration).delete()
    db_session.commit()


def test_list_integration(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get("/v1/integrations/", headers={"x-api-key": dummy_api_key})
    print(response.json())
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 2


def test_list_integration_with_app_name(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[sql_models.App],
) -> None:
    # get GOOGLE app's app id
    google_app_id = next(app.id for app in dummy_apps if app.name == GOOGLE)

    # list GOOGLE app integration of the project
    response = test_client.get(
        f"/v1/integrations/?app_name={GOOGLE}", headers={"x-api-key": dummy_api_key}
    )

    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_id"] == str(google_app_id)


def test_list_integration_with_non_existent_app_name(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"/v1/integrations/?app_name={NON_EXISTENT_APP}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 0
