from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Project
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.app import AppBasic
from aipolabs.server import config


def test_search_apps_with_intent(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_app_github: App,
    dummy_app_google: App,
    dummy_api_key: str,
) -> None:
    # try with intent to find GITHUB app
    search_params = {
        "intent": "i want to create a new code repo for my project",
        "categories": [],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    assert apps[0].name == dummy_app_github.name

    # try with intent to find google app
    search_params["intent"] = "i want to search the web"
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    assert apps[0].name == dummy_app_google.name


def test_search_apps_without_intent(
    test_client: TestClient, dummy_apps: list[App], dummy_api_key: str
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search", headers={"x-api-key": dummy_api_key}
    )

    assert response.status_code == 200, response.json()

    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)


def test_search_apps_with_categories(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_aipolabs_test: App,
) -> None:
    search_params = {
        "intent": None,
        "categories": ["testcategory"],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1
    assert apps[0].name == dummy_app_aipolabs_test.name


def test_search_apps_with_categories_and_intent(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_app_google: App,
    dummy_app_github: App,
) -> None:
    search_params = {
        "intent": "i want to create a new code repo for my project",
        "categories": ["testcategory-2"],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 2
    assert apps[0].name == dummy_app_github.name
    assert apps[1].name == dummy_app_google.name


def test_search_apps_pagination(
    test_client: TestClient, dummy_apps: list[App], dummy_api_key: str
) -> None:
    assert len(dummy_apps) > 2

    search_params: dict[str, Any] = {
        "intent": None,
        "categories": [],
        "limit": len(dummy_apps) - 1,
        "offset": 0,
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    search_params["offset"] = len(dummy_apps) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1


def test_search_apps_with_disabled_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_api_key: str,
) -> None:
    crud.apps.set_app_enabled_status(db_session, dummy_apps[0].id, False)
    db_session.commit()

    # disabled app should not be returned
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    # revert changes
    crud.apps.set_app_enabled_status(db_session, dummy_apps[0].id, True)
    db_session.commit()


def test_search_apps_with_private_apps(
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
        f"{config.ROUTER_PREFIX_APPS}/search",
        params={},
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    # private app should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params={},
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)

    # revert changes
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    crud.apps.set_app_visibility(db_session, dummy_apps[0].id, Visibility.PUBLIC)
    db_session.commit()
