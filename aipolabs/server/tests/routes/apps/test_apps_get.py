from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.schemas.app import AppBasicWithFunctions
from aipolabs.server import config

NON_EXISTENT_APP_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_get_app(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_github: sql_models.App,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_app_github.id}",
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    app = AppBasicWithFunctions.model_validate(response.json())
    assert app.name == dummy_app_github.name
    assert len(app.functions) > 0


def test_get_non_existent_app(test_client: TestClient, dummy_api_key: str) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{NON_EXISTENT_APP_ID}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 404, response.json()


def test_get_disabled_app(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[sql_models.App],
    dummy_api_key: str,
) -> None:
    crud.set_app_enabled_status(db_session, dummy_apps[0].id, False)
    db_session.commit()

    # disabled app should not be returned
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_apps[0].id}", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 403, response.json()

    # revert changes
    crud.set_app_enabled_status(db_session, dummy_apps[0].id, True)
    db_session.commit()


def test_get_private_app(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[sql_models.App],
    dummy_project: sql_models.Project,
    dummy_api_key: str,
) -> None:
    # private app should not be reachable for project with only public access
    crud.set_app_visibility(db_session, dummy_apps[0].id, sql_models.Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_apps[0].id}",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 403, response.json()

    # private app should be reachable for project with private access
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/{dummy_apps[0].id}",
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    app = AppBasicWithFunctions.model_validate(response.json())
    assert app.name == dummy_apps[0].name

    # revert changes
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PUBLIC)
    crud.set_app_visibility(db_session, dummy_apps[0].id, sql_models.Visibility.PUBLIC)
    db_session.commit()


# TODO: test app with private and disabled functions, see if functions are filtered correctly
