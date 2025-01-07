from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.schemas.app import AppDetails
from aipolabs.server import config


def test_list_apps(
    test_client: TestClient,
    dummy_apps: list[sql_models.App],
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    query_params = {
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    # assert each app has the correct functions
    for app in apps:
        assert len(app.functions) == len([f for f in dummy_functions if f.app_id == app.id])


def test_list_apps_pagination(
    test_client: TestClient, dummy_apps: list[sql_models.App], dummy_api_key: str
) -> None:
    assert len(dummy_apps) > 2

    query_params: dict[str, Any] = {
        "limit": len(dummy_apps) - 1,
        "offset": 0,
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/", params=query_params, headers={"x-api-key": dummy_api_key}
    )

    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    query_params["offset"] = len(dummy_apps) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1


def test_list_apps_with_private_apps(
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
        f"{config.ROUTER_PREFIX_APPS}/",
        params={},
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    # private app should be reachable for project with private access
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/",
        params={},
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)

    # revert changes
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PUBLIC)
    crud.set_app_visibility(db_session, dummy_apps[0].id, sql_models.Visibility.PUBLIC)
    db_session.commit()
