from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Project
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.app import AppBasicWithFunctions
from aipolabs.server import config

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_get_app(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_github: App,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_app_github.id}",
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == status.HTTP_200_OK
    app = AppBasicWithFunctions.model_validate(response.json())
    assert app.name == dummy_app_github.name
    assert len(app.functions) > 0


def test_get_non_existent_app(test_client: TestClient, dummy_api_key: str) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{NON_EXISTENT_APP_ID}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_inactive_app(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_api_key: str,
) -> None:
    crud.apps.set_app_active_status(db_session, dummy_apps[0].id, False)
    db_session.commit()

    # inactive app should not be returned
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_apps[0].id}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # revert changes
    crud.apps.set_app_active_status(db_session, dummy_apps[0].id, True)
    db_session.commit()


def test_get_private_app(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project: Project,
    dummy_api_key: str,
) -> None:
    # private app should not be reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_apps[0].id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_apps[0].id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # private app should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_apps[0].id}",
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == status.HTTP_200_OK
    app = AppBasicWithFunctions.model_validate(response.json())
    assert app.name == dummy_apps[0].name

    # revert changes
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    crud.apps.set_app_visibility(db_session, dummy_apps[0].id, Visibility.PUBLIC)
    db_session.commit()
