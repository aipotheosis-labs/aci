from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.schemas.integrations import IntegrationPublic

GOOGLE = "GOOGLE"
NON_EXISTENT_APP = "NON_EXISTENT_APP"


@pytest.fixture(autouse=True)
def cleanup_integrations(db_session: Session) -> Generator[None, None, None]:
    """Automatically clean up integrations table after each test"""
    yield
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


def test_add_integration(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    # success case
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    IntegrationPublic.model_validate(response.json())

    # failure case: App already integrated
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "App is already integrated to the project"


def test_add_integration_security_scheme_not_supported(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.HTTP_BASIC}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "Security scheme is not supported by the app"


def test_add_integration_app_not_found(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    payload = {"app_name": NON_EXISTENT_APP, "security_scheme": SecurityScheme.OAUTH2}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "App not found"


def test_add_integration_app_not_enabled(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
) -> None:
    # disable the app
    crud.set_app_enabled_status_by_name(db_session, GOOGLE, False)
    db_session.commit()

    # try to add integration
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "App is not enabled"

    # re-enable the app
    crud.set_app_enabled_status_by_name(db_session, GOOGLE, True)
    db_session.commit()


def test_add_integration_project_does_not_have_access(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
) -> None:
    # set the app to private
    crud.set_app_visibility_by_name(db_session, GOOGLE, Visibility.PRIVATE)
    db_session.commit()

    # try to add integration
    payload = {"app_name": GOOGLE, "security_scheme": SecurityScheme.OAUTH2}
    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "Project does not have access to this app."

    # revert changes
    crud.set_app_visibility_by_name(db_session, GOOGLE, Visibility.PUBLIC)
    db_session.commit()
