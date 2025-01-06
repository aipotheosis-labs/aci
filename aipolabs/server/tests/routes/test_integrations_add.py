from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.schemas.integrations import IntegrationCreate, IntegrationPublic

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True)
def cleanup_integrations(db_session: Session) -> Generator[None, None, None]:
    """Automatically clean up integrations table after each test"""
    yield
    db_session.query(sql_models.Integration).delete()
    db_session.commit()


def test_add_integration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[sql_models.App],
) -> None:
    # success case
    dummy_app = dummy_apps[0]
    body = IntegrationCreate(app_id=dummy_app.id, security_scheme=SecurityScheme.OAUTH2)

    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    IntegrationPublic.model_validate(response.json())

    # failure case: App already integrated
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "App is already integrated to the project"


def test_add_integration_security_scheme_not_supported(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[sql_models.App],
) -> None:
    dummy_app = dummy_apps[0]
    body = IntegrationCreate(app_id=dummy_app.id, security_scheme=SecurityScheme.HTTP_BASIC)
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "Security scheme is not supported by the app"


def test_add_integration_app_not_found(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    body = IntegrationCreate(app_id=NON_EXISTENT_APP_ID, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "App not found"


def test_add_integration_app_not_enabled(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
    dummy_google_app: sql_models.App,
) -> None:
    # disable the app
    crud.set_app_enabled_status(db_session, dummy_google_app.id, False)
    db_session.commit()

    # try to add integration
    body = IntegrationCreate(app_id=dummy_google_app.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "App is not enabled"

    # re-enable the app
    crud.set_app_enabled_status(db_session, dummy_google_app.id, True)
    db_session.commit()


def test_add_integration_project_does_not_have_access(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
    dummy_google_app: sql_models.App,
) -> None:
    # set the app to private
    crud.set_app_visibility(db_session, dummy_google_app.id, Visibility.PRIVATE)
    db_session.commit()

    # try to add integration
    body = IntegrationCreate(app_id=dummy_google_app.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        "/v1/integrations/", json=body.model_dump(mode="json"), headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "Project does not have access to this app."

    # revert changes
    crud.set_app_visibility(db_session, dummy_google_app.id, Visibility.PUBLIC)
    db_session.commit()
