import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Agent, App, Project
from aci.common.enums import Visibility
from aci.common.schemas.app import AppBasic, AppsSearch
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.server import config


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_with_intent(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_app_github: App,
    dummy_app_google: App,
    dummy_api_key_1: str,
    include_functions: bool,
) -> None:
    # try with intent to find GITHUB app
    apps_search = AppsSearch(
        intent="i want to create a new code repo for my project",
        limit=100,
        offset=0,
        include_functions=include_functions,
    )

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    assert apps[0].name == dummy_app_github.name

    # try with intent to find google app
    apps_search.intent = "i want to search the web"
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    assert apps[0].name == dummy_app_google.name


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_without_intent(
    test_client: TestClient, dummy_apps: list[App], dummy_api_key_1: str, include_functions: bool
) -> None:
    apps_search = AppsSearch(
        limit=100,
        offset=0,
        include_functions=include_functions,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK

    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_with_categories(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aci_test: App,
    include_functions: bool,
) -> None:
    apps_search = AppsSearch(
        categories=["testcategory"],
        limit=100,
        offset=0,
        include_functions=include_functions,
    )

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1
    assert apps[0].name == dummy_app_aci_test.name


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_with_categories_and_intent(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_google: App,
    dummy_app_github: App,
    include_functions: bool,
) -> None:
    apps_search = AppsSearch(
        intent="i want to create a new code repo for my project",
        categories=["testcategory-2"],
        limit=100,
        offset=0,
        include_functions=include_functions,
    )

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 2
    assert apps[0].name == dummy_app_github.name
    assert apps[1].name == dummy_app_google.name


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_pagination(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_api_key_1: str,
    include_functions: bool,
) -> None:
    assert len(dummy_apps) > 2

    apps_search = AppsSearch(
        intent=None,
        limit=len(dummy_apps) - 1,
        offset=0,
        include_functions=include_functions,
    )

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    apps_search.offset = len(dummy_apps) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_with_inactive_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_api_key_1: str,
    include_functions: bool,
) -> None:
    crud.apps.set_app_active_status(db_session, dummy_apps[0].name, False)
    db_session.commit()

    apps_search = AppsSearch(
        intent=None,
        limit=100,
        offset=0,
        include_functions=include_functions,
    )

    # inactive app should not be returned
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_with_private_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_project_1: Project,
    dummy_api_key_1: str,
    include_functions: bool,
) -> None:
    # private app should not be reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_apps[0].name, Visibility.PRIVATE)
    db_session.commit()

    apps_search = AppsSearch(
        intent=None,
        limit=100,
        offset=0,
        include_functions=include_functions,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
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
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)


@pytest.mark.parametrize("include_functions", [True, False])
def test_search_apps_allowed_apps_only(
    db_session: Session,
    test_client: TestClient,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_agent_1_with_no_apps_allowed: Agent,
    include_functions: bool,
) -> None:
    apps_search = AppsSearch(
        allowed_apps_only=True,
        limit=100,
        offset=0,
        include_functions=include_functions,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 0, "Should not return any apps because the agent has no allowed apps"

    # update the agent to allow only the google app
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [
        dummy_app_configuration_oauth2_google_project_1.app_name
    ]
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=apps_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )

    assert response.status_code == status.HTTP_200_OK
    apps = [AppBasic.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1, "Should return the one allowed app of the agent"
    assert apps[0].name == dummy_app_configuration_oauth2_google_project_1.app_name, (
        "Returned app and allowed app are not the same"
    )
