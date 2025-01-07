from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.schemas.function import FunctionBasic
from aipolabs.server import config


def test_search_functions_with_disabled_functions(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    # disabled functions should not be returned
    crud.set_function_enabled_status(db_session, dummy_functions[0].id, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions) - 1

    # revert changes
    crud.set_function_enabled_status(db_session, dummy_functions[0].id, True)
    db_session.commit()


def test_search_functions_with_disabled_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    # all functions (enabled or not) under disabled apps should not be returned
    crud.set_app_enabled_status(db_session, dummy_functions[0].app_id, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]

    disabled_functions_count = sum(
        function.app_id == dummy_functions[0].app_id for function in dummy_functions
    )
    assert disabled_functions_count > 0, "there should be at least one disabled function"
    assert (
        len(functions) == len(dummy_functions) - disabled_functions_count
    ), "all functions under disabled apps should not be returned"

    # revert changes
    crud.set_app_enabled_status(db_session, dummy_functions[0].app_id, True)
    db_session.commit()


def test_search_functions_with_private_functions(
    db_session: Session,
    test_client: TestClient,
    dummy_project: sql_models.Project,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    # private functions should not be reachable for project with only public access
    crud.set_function_visibility(db_session, dummy_functions[0].id, sql_models.Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions) - 1

    # private functions should be reachable for project with private access
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)

    # revert changes
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PUBLIC)
    crud.set_function_visibility(db_session, dummy_functions[0].id, sql_models.Visibility.PUBLIC)
    db_session.commit()


def test_search_functions_with_private_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_project: sql_models.Project,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    # all functions (public and private) under private apps should not be reachable for project with only public access
    crud.set_app_visibility(db_session, dummy_functions[0].app_id, sql_models.Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]

    private_functions_count = sum(
        function.app_id == dummy_functions[0].app_id for function in dummy_functions
    )
    assert private_functions_count > 0, "there should be at least one private function"
    assert (
        len(functions) == len(dummy_functions) - private_functions_count
    ), "all functions under private apps should not be returned"

    # all functions (public and private) under private apps should be reachable for project with private access
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)

    # revert changes
    crud.set_app_visibility(db_session, dummy_functions[0].app_id, sql_models.Visibility.PUBLIC)
    crud.set_project_visibility_access(db_session, dummy_project.id, sql_models.Visibility.PUBLIC)
    db_session.commit()


def test_search_functions_with_app_ids(
    test_client: TestClient, dummy_functions: list[sql_models.Function], dummy_api_key: str
) -> None:
    search_param = {
        "app_ids": [dummy_functions[0].app_id, dummy_functions[1].app_id],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
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
        function.app_id in [dummy_functions[0].app_id, dummy_functions[1].app_id]
        for function in dummy_functions
    )


def test_search_functions_with_intent(
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_function_github__create_repository: sql_models.Function,
    dummy_function_google__calendar_create_event: sql_models.Function,
    dummy_api_key: str,
) -> None:

    # intent1: create repo
    search_param = {
        "intent": "i want to create a new code repo for my project",
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
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
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)
    assert functions[0].name == dummy_function_google__calendar_create_event.name


def test_search_functions_with_app_ids_and_intent(
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
    dummy_app_github: sql_models.App,
) -> None:
    search_param = {
        "app_ids": [dummy_app_github.id],
        "intent": "i want to create a new code repo for my project",
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    # only functions from the given app ids should be returned
    for function in functions:
        assert function.name.startswith(dummy_app_github.name)
    # total number of functions should be the sum of functions from the given app ids
    assert len(functions) == sum(
        function.app_id == dummy_app_github.id for function in dummy_functions
    )
    assert functions[0].name.startswith(dummy_app_github.name)


def test_search_functions_pagination(
    test_client: TestClient, dummy_functions: list[sql_models.Function], dummy_api_key: str
) -> None:
    assert len(dummy_functions) > 2

    search_param = {
        "limit": len(dummy_functions) - 1,
        "offset": 0,
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions) - 1

    search_param["offset"] = len(dummy_functions) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=search_param,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    functions = [
        FunctionBasic.model_validate(response_function) for response_function in response.json()
    ]
    assert len(functions) == 1
