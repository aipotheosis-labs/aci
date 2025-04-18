from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import App, Project
from aci.common.enums import Visibility
from aci.common.schemas.app import AppDetails
from aci.server import config

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_get_app(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_github: App,
) -> None:
    app_name = dummy_app_github.name
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{app_name}",
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    app = AppDetails.model_validate(response.json())
    assert app.name == dummy_app_github.name
    assert len(app.functions) > 0


def test_get_non_existent_app(test_client: TestClient, dummy_api_key_1: str) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{NON_EXISTENT_APP_ID}",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_inactive_app(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_api_key_1: str,
) -> None:
    crud.apps.set_app_active_status(db_session, dummy_apps[0].name, False)
    db_session.commit()

    app_name = dummy_apps[0].name
    # inactive app should not be returned
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{app_name}",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_private_app(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
    dummy_api_key_1: str,
) -> None:
    # private app should not be reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_apps[0].name, Visibility.PRIVATE)
    db_session.commit()

    app_name = dummy_apps[0].name
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{app_name}",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # private app should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{app_name}",
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    app = AppDetails.model_validate(response.json())
    assert app.name == dummy_apps[0].name
