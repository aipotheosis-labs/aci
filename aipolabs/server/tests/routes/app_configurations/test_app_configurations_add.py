from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, AppConfiguration
from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)
from aipolabs.server import config

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture(autouse=True)
def cleanup(db_session: Session) -> Generator[None, None, None]:
    """Automatically clean up app configurations table after each test"""
    yield
    db_session.query(AppConfiguration).delete()
    db_session.commit()


def test_create_app_configuration(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[App],
) -> None:
    # success case
    dummy_app = dummy_apps[0]
    body = AppConfigurationCreate(app_id=dummy_app.id, security_scheme=SecurityScheme.OAUTH2)

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    AppConfigurationPublic.model_validate(response.json())

    # failure case: App already configured
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert str(response.json()["error"]).startswith("App configuration already exists")


def test_create_app_configuration_security_scheme_not_supported(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_apps: list[App],
) -> None:
    dummy_app = dummy_apps[0]
    body = AppConfigurationCreate(app_id=dummy_app.id, security_scheme=SecurityScheme.HTTP_BASIC)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
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
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "App not found"


def test_create_app_configuration_app_not_enabled(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
    dummy_app_google: App,
) -> None:
    # disable the app
    crud.apps.set_app_enabled_status(db_session, dummy_app_google.id, False)
    db_session.commit()

    # try creating app configuration
    body = AppConfigurationCreate(app_id=dummy_app_google.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "App is not enabled"

    # re-enable the app
    crud.apps.set_app_enabled_status(db_session, dummy_app_google.id, True)
    db_session.commit()


def test_create_app_configuration_project_does_not_have_access(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key: str,
    dummy_app_google: App,
) -> None:
    # set the app to private
    crud.apps.set_app_visibility(db_session, dummy_app_google.id, Visibility.PRIVATE)
    db_session.commit()

    # try creating app configuration
    body = AppConfigurationCreate(app_id=dummy_app_google.id, security_scheme=SecurityScheme.OAUTH2)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "Project does not have access to this app."

    # revert changes
    crud.apps.set_app_visibility(db_session, dummy_app_google.id, Visibility.PUBLIC)
    db_session.commit()
