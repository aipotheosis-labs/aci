from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Agent, App, Function, Project
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.app_configurations import AppConfigurationPublic
from aipolabs.common.schemas.function import FunctionBasic
from aipolabs.server import config


def test_search_functions_with_inactive_functions(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
) -> None:
    # inactive functions should not be returned
    crud.functions.set_function_active_status(db_session, dummy_functions[0].name, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions) - 1


def test_search_functions_with_inactive_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
) -> None:
    # all functions (active or not) under inactive apps should not be returned
    crud.apps.set_app_active_status(db_session, dummy_functions[0].app.name, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]

    inactive_functions_count = sum(
        function.app.name == dummy_functions[0].app.name for function in dummy_functions
    )
    assert inactive_functions_count > 0, "there should be at least one inactive function"
    assert len(functions) == len(dummy_functions) - inactive_functions_count, (
        "no functions should be returned under inactive apps"
    )


def test_search_functions_with_private_functions(
    db_session: Session,
    test_client: TestClient,
    dummy_project_1: Project,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
) -> None:
    # private functions should not be reachable for project with only public access
    crud.functions.set_function_visibility(db_session, dummy_functions[0].name, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions) - 1

    # private functions should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)


def test_search_functions_with_private_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_project_1: Project,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
) -> None:
    # all functions (public and private) under private apps should not be
    # reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_functions[0].app.name, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]

    private_functions_count = sum(
        function.app.name == dummy_functions[0].app.name for function in dummy_functions
    )
    assert private_functions_count > 0, "there should be at least one private function"
    assert len(functions) == len(dummy_functions) - private_functions_count, (
        "all functions under private apps should not be returned"
    )

    # all functions (public and private) under private apps should be reachable
    # for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)


def test_search_functions_with_app_names(
    test_client: TestClient, dummy_functions: list[Function], dummy_api_key_1: str
) -> None:
    search_param: dict[str, str | list[str] | int] = {
        "app_names": [dummy_functions[0].app.name, dummy_functions[1].app.name],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    # only functions from the given app ids should be returned
    for function in functions:
        assert function.name.startswith(dummy_functions[0].app.name) or function.name.startswith(
            dummy_functions[1].app.name
        )
    # total number of functions should be the sum of functions from the given app ids
    assert len(functions) == sum(
        function.app.name in [dummy_functions[0].app.name, dummy_functions[1].app.name]
        for function in dummy_functions
    )


def test_search_functions_with_intent(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_function_github__create_repository: Function,
    dummy_function_google__calendar_create_event: Function,
    dummy_api_key_1: str,
) -> None:
    # intent1: create repo
    search_param: dict[str, str | int] = {
        "intent": "i want to create a new code repo for my project",
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)
    assert functions[0].name == dummy_function_github__create_repository.name

    # intent2: upload file
    search_param["intent"] = "add this meeting to my calendar"
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)
    assert functions[0].name == dummy_function_google__calendar_create_event.name


def test_search_functions_with_app_names_and_intent(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    dummy_app_github: App,
) -> None:
    search_param: dict[str, str | list[str] | int] = {
        "app_names": [dummy_app_github.name],
        "intent": "i want to create a new code repo for my project",
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    # only functions from the given app ids should be returned
    for function in functions:
        assert function.name.startswith(dummy_app_github.name)
    # total number of functions should be the sum of functions from the given app ids
    assert len(functions) == sum(
        function.app.name == dummy_app_github.name for function in dummy_functions
    )
    assert functions[0].name.startswith(dummy_app_github.name)


def test_search_functions_pagination(
    test_client: TestClient, dummy_functions: list[Function], dummy_api_key_1: str
) -> None:
    assert len(dummy_functions) > 2

    search_param = {
        "limit": len(dummy_functions) - 1,
        "offset": 0,
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions) - 1

    search_param["offset"] = len(dummy_functions) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == 1


def test_search_functions_allowed_apps_only_true(
    db_session: Session,
    test_client: TestClient,
    dummy_app_configuration_oauth2_aipolabs_test_project_1: AppConfigurationPublic,
    dummy_app_aipolabs_test: App,
    dummy_agent_1_with_no_apps_allowed: Agent,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={"allowed_apps_only": True},
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == 0, (
        "no functions should be returned because the agent is not allowed to access any app"
    )

    # update the agent to allow access to the app
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [dummy_app_aipolabs_test.name]
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={"allowed_apps_only": True},
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_app_aipolabs_test.functions), (
        "should return all functions from the allowed app"
    )
    dummy_app_function_names = [function.name for function in dummy_app_aipolabs_test.functions]
    assert all(function.name in dummy_app_function_names for function in functions)


def test_search_functions_allowed_apps_only_false(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_agent_1_with_no_apps_allowed: Agent,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={"allowed_apps_only": False},
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions), (
        "should return all functions because allowed_apps_only is False"
    )


def test_search_functions_with_app_names_and_allowed_apps_only(
    db_session: Session,
    test_client: TestClient,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
    dummy_app_github: App,
    dummy_app_google: App,
    dummy_agent_1_with_no_apps_allowed: Agent,
) -> None:
    # set the agent to allow access to one of the apps
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [dummy_app_github.name]
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={
            "app_names": [dummy_app_github.name, dummy_app_google.name],
            "allowed_apps_only": True,
        },
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_app_github.functions), (
        "should only return functions from the allowed app"
    )
    dummy_app_github_function_names = [function.name for function in dummy_app_github.functions]
    assert all(function.name in dummy_app_github_function_names for function in functions), (
        "returned functions should be from the allowed app"
    )

    # set the agent to allow access to both apps
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [dummy_app_github.name, dummy_app_google.name]
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params={
            "app_names": [dummy_app_github.name, dummy_app_google.name],
            "allowed_apps_only": True,
        },
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_app_google.functions) + len(dummy_app_github.functions), (
        "should return functions from both allowed apps"
    )
