from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Project
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.app import AppBasic
from aipolabs.common.schemas.app_configurations import AppConfigurationPublic
from aipolabs.server import config


def test_search_apps_with_intent(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_app_github: App,
    dummy_app_google: App,
    dummy_api_key_1: str,
) -> None:
    # try with intent to find GITHUB app
    search_params: dict[str, str | list[str] | int] = {
        "intent": "i want to create a new code repo for my project",
        "categories": [],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    assert apps[0].name == dummy_app_github.name

    # try with intent to find google app
    search_params["intent"] = "i want to search the web"
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    assert apps[0].name == dummy_app_google.name


def test_search_apps_without_intent(
    test_client: TestClient, dummy_apps: list[App], dummy_api_key_1: str
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search", headers={"x-api-key": dummy_api_key_1}
    )

    assert response.status_code == status.HTTP_200_OK

    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)


def test_search_apps_with_categories(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aipolabs_test: App,
) -> None:
    search_params: dict[str, str | list[str] | int | None] = {
        "intent": None,
        "categories": ["testcategory"],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1
    assert apps[0].name == dummy_app_aipolabs_test.name


def test_search_apps_with_categories_and_intent(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_google: App,
    dummy_app_github: App,
) -> None:
    search_params: dict[str, str | list[str] | int] = {
        "intent": "i want to create a new code repo for my project",
        "categories": ["testcategory-2"],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 2
    assert apps[0].name == dummy_app_github.name
    assert apps[1].name == dummy_app_google.name


def test_search_apps_pagination(
    test_client: TestClient, dummy_apps: list[App], dummy_api_key_1: str
) -> None:
    assert len(dummy_apps) > 2

    search_params: dict[str, str | list[str] | int | None] = {
        "intent": None,
        "categories": [],
        "limit": len(dummy_apps) - 1,
        "offset": 0,
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    search_params["offset"] = len(dummy_apps) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1


def test_search_apps_with_inactive_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_api_key_1: str,
) -> None:
    crud.apps.set_app_active_status(db_session, dummy_apps[0].name, False)
    db_session.commit()

    # inactive app should not be returned
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1


def test_search_apps_with_private_apps(
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
        f"{config.ROUTER_PREFIX_APPS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    # private app should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)


def test_search_apps_configured_only(
    test_client: TestClient,
    dummy_app_google: App,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_api_key_1: str,
) -> None:
    # Test with configured_only=True
    search_params = {
        "configured_only": True,
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1, "Should only return the one configured app"
    assert apps[0].name == dummy_app_google.name, "Returned app and configured app are not the same"


def test_search_apps_configured_only_with_none_configured(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
    dummy_api_key_1: str,
) -> None:
    search_params = {
        "configured_only": True,
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 0, "Should not return any apps"


def test_search_apps_configured_only_exclude_apps_from_other_projects(
    db_session: Session,
    test_client: TestClient,
    dummy_app_google: App,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_github_project_2: AppConfigurationPublic,
    dummy_api_key_1: str,
) -> None:
    search_params = {
        "configured_only": True,
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1, "Should only return one app"
    assert apps[0].name == dummy_app_google.name, "Returned app and configured app are not the same"
