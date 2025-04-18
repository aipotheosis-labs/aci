from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import App
from aci.common.enums import SecurityScheme, Visibility
from aci.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)
from aci.server import config

NON_EXISTENT_APP_NAME = "non-existent-app"


def test_create_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_apps: list[App],
) -> None:
    # success case
    dummy_app = dummy_apps[0]
    body = AppConfigurationCreate(app_name=dummy_app.name, security_scheme=SecurityScheme.OAUTH2)

    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    AppConfigurationPublic.model_validate(response.json())

    # failure case: App already configured
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert str(response.json()["error"]).startswith("App configuration already exists")


def test_create_app_configuration_security_scheme_not_supported(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_apps: list[App],
) -> None:
    dummy_app = dummy_apps[0]
    body = AppConfigurationCreate(
        app_name=dummy_app.name, security_scheme=SecurityScheme.HTTP_BASIC
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert str(response.json()["error"]).startswith(
        "Specified security scheme not supported by the app"
    )


def test_create_app_configuration_app_not_found(
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    body = AppConfigurationCreate(
        app_name=NON_EXISTENT_APP_NAME, security_scheme=SecurityScheme.OAUTH2
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App not found")


def test_create_app_configuration_app_not_enabled(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key_1: str,
    dummy_app_google: App,
) -> None:
    crud.apps.set_app_active_status(db_session, dummy_app_google.name, False)
    db_session.commit()

    # try creating app configuration
    body = AppConfigurationCreate(
        app_name=dummy_app_google.name, security_scheme=SecurityScheme.OAUTH2
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App not found")


def test_create_app_configuration_project_does_not_have_access(
    test_client: TestClient,
    db_session: Session,
    dummy_api_key_1: str,
    dummy_app_google: App,
) -> None:
    # set the app to private
    crud.apps.set_app_visibility(db_session, dummy_app_google.name, Visibility.PRIVATE)
    db_session.commit()

    # try creating app configuration
    body = AppConfigurationCreate(
        app_name=dummy_app_google.name, security_scheme=SecurityScheme.OAUTH2
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}",
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App not found")
