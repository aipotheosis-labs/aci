from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True)
def cleanup(db_session: Session) -> Generator[None, None, None]:
    """Automatically clean up app configurations table after each test"""
    yield
    db_session.query(sql_models.AppConfiguration).delete()
    db_session.commit()


def test_create_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[sql_models.App],
) -> None:
    # success case
    dummy_app = dummy_apps[0]
    body = AppConfigurationCreate(app_id=dummy_app.id, security_scheme=SecurityScheme.OAUTH2)

    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    AppConfigurationPublic.model_validate(response.json())

    # failure case: App already configured
    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "App is already configured for the project"


def test_create_app_configuration_security_scheme_not_supported(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[sql_models.App],
) -> None:
    dummy_app = dummy_apps[0]
    body = AppConfigurationCreate(app_id=dummy_app.id, security_scheme=SecurityScheme.HTTP_BASIC)
    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "Security scheme is not supported by the app"


def test_create_app_configuration_app_not_found(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    body = AppConfigurationCreate(app_id=NON_EXISTENT_APP_ID, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "App not found"


def test_create_app_configuration_app_not_enabled(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
    dummy_google_app: sql_models.App,
) -> None:
    # disable the app
    crud.set_app_enabled_status(db_session, dummy_google_app.id, False)
    db_session.commit()

    # try creating app configuration
    body = AppConfigurationCreate(app_id=dummy_google_app.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "App is not enabled"

    # re-enable the app
    crud.set_app_enabled_status(db_session, dummy_google_app.id, True)
    db_session.commit()


def test_create_app_configuration_project_does_not_have_access(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
    dummy_google_app: sql_models.App,
) -> None:
    # set the app to private
    crud.set_app_visibility(db_session, dummy_google_app.id, Visibility.PRIVATE)
    db_session.commit()

    # try creating app configuration
    body = AppConfigurationCreate(app_id=dummy_google_app.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        "/v1/app-configurations/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "Project does not have access to this app."

    # revert changes
    crud.set_app_visibility(db_session, dummy_google_app.id, Visibility.PUBLIC)
    db_session.commit()
