from typing import Any

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, AppConfiguration, Project
from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.schemas.app import AppBasic
from aipolabs.server import config


def test_search_apps_with_intent(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_app_github: App,
    dummy_app_google: App,
    dummy_api_key_1: str,
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
    search_params = {
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
    search_params = {
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

    search_params: dict[str, Any] = {
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
    crud.apps.set_app_active_status(db_session, dummy_apps[0].id, False)
    db_session.commit()

    # inactive app should not be returned
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search", params={}, headers={"x-api-key": dummy_api_key_1}
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
    crud.apps.set_app_visibility(db_session, dummy_apps[0].id, Visibility.PRIVATE)
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
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
    dummy_api_key_1: str,
) -> None:
    # Create an app configuration for the first app
    app_config = AppConfiguration(
        project_id=dummy_project_1.id,
        app_id=dummy_apps[0].id,
        security_scheme=SecurityScheme.API_KEY,
        security_config_overrides={},
        enabled=True,
        all_functions_enabled=True,
        enabled_functions=[],
    )
    db_session.add(app_config)
    db_session.commit()

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
    assert len(apps) == 1  # Should only return the one configured app
    assert apps[0].name == dummy_apps[0].name  # assert that the correct app is returned


def test_search_apps_configured_only_with_none_configured(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
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
    assert len(apps) == 0  # Should only return the one configured app


def test_search_apps_configured_only_with_multiple_configurations(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
    dummy_project_2: Project,
    dummy_api_key_1: str,
) -> None:
    # Configure the same app in multiple projects
    app_config_1 = AppConfiguration(
        project_id=dummy_project_1.id,
        app_id=dummy_apps[0].id,
        security_scheme=SecurityScheme.API_KEY,
        security_config_overrides={},
        enabled=True,
        all_functions_enabled=True,
        enabled_functions=[],
    )
    app_config_2 = AppConfiguration(
        project_id=dummy_project_2.id,
        app_id=dummy_apps[0].id,
        security_scheme=SecurityScheme.API_KEY,
        security_config_overrides={},
        enabled=True,
        all_functions_enabled=True,
        enabled_functions=[],
    )
    db_session.add_all([app_config_1, app_config_2])
    db_session.commit()

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
    assert len(apps) == 1  # Should still only return one app despite multiple configurations
    assert apps[0].name == dummy_apps[0].name  # assert that the correct app is returned


def test_search_apps_with_specific_functions_enabled(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
    dummy_api_key_1: str,
) -> None:
    # Create configuration with specific functions enabled
    app_config = AppConfiguration(
        project_id=dummy_project_1.id,
        app_id=dummy_apps[0].id,
        security_scheme=SecurityScheme.API_KEY,
        security_config_overrides={},
        enabled=True,
        all_functions_enabled=False,  # Only specific functions enabled
        enabled_functions=[func.id for func in dummy_apps[0].functions],
    )
    db_session.add(app_config)
    db_session.commit()

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
    assert len(apps) == 1
    assert apps[0].name == dummy_apps[0].name
