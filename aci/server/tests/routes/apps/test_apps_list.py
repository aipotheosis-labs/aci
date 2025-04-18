from typing import Any

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import App, Function, Project
from aci.common.enums import Visibility
from aci.common.schemas.app import AppDetails
from aci.server import config


def test_list_apps(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_functions: list[Function],
    dummy_api_key_1: str,
) -> None:
    query_params = {
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}",
        params=query_params,
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    # assert each app has the correct functions
    for app in apps:
        assert len(app.functions) == len([f for f in dummy_functions if f.app.name == app.name])


def test_list_apps_pagination(
    test_client: TestClient, dummy_apps: list[App], dummy_api_key_1: str
) -> None:
    assert len(dummy_apps) > 2

    query_params: dict[str, Any] = {
        "limit": len(dummy_apps) - 1,
        "offset": 0,
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}",
        params=query_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    query_params["offset"] = len(dummy_apps) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}",
        params=query_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1


def test_list_apps_with_private_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
    dummy_api_key_1: str,
) -> None:
    # private app should not be reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_apps[0].name, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    # private app should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)


def test_list_apps_with_app_names(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_api_key_1: str,
) -> None:
    expected_app_names = [dummy_apps[0].name, dummy_apps[1].name]
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}",
        params={"app_names": expected_app_names},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    returned_app_names = [app.name for app in apps]
    # sort both lists by app id for comparison
    assert sorted(returned_app_names) == sorted(expected_app_names)
