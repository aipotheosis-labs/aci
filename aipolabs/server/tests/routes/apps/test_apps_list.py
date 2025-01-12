from typing import Any

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Function, Project
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.app import AppDetails
from aipolabs.server import config


def test_list_apps(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_functions: list[Function],
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
    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    # assert each app has the correct functions
    for app in apps:
        assert len(app.functions) == len([f for f in dummy_functions if f.app_id == app.id])


def test_list_apps_pagination(
    test_client: TestClient, dummy_apps: list[App], dummy_api_key: str
) -> None:
    assert len(dummy_apps) > 2

    query_params: dict[str, Any] = {
        "limit": len(dummy_apps) - 1,
        "offset": 0,
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/", params=query_params, headers={"x-api-key": dummy_api_key}
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    query_params["offset"] = len(dummy_apps) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1


def test_list_apps_with_private_apps(
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
        f"{config.ROUTER_PREFIX_APPS}/",
        params={},
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    # private app should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/",
        params={},
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)

    # revert changes
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    crud.apps.set_app_visibility(db_session, dummy_apps[0].id, Visibility.PUBLIC)
    db_session.commit()
