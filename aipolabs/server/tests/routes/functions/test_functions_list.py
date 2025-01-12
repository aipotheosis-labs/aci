from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Function, Project
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.function import FunctionDetails
from aipolabs.server import config


def test_list_all_functions(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key: str,
) -> None:
    query_params = {
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]
    assert len(functions) == len(dummy_functions)


def test_list_all_functions_pagination(
    test_client: TestClient, dummy_functions: list[Function], dummy_api_key: str
) -> None:
    query_params = {
        "limit": len(dummy_functions) - 1,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]
    assert len(functions) == len(dummy_functions) - 1

    query_params["offset"] = len(dummy_functions) - 1
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]
    assert len(functions) == 1


def test_list_functions_with_app_ids(
    test_client: TestClient,
    dummy_apps: list[App],
    dummy_functions: list[Function],
    dummy_api_key: str,
) -> None:
    query_params = {
        "app_ids": [dummy_apps[0].id, dummy_apps[1].id],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]
    assert len(functions) == sum(
        function.app_id in [dummy_apps[0].id, dummy_apps[1].id] for function in dummy_functions
    )


def test_list_functions_with_private_functions(
    db_session: Session,
    test_client: TestClient,
    dummy_project: Project,
    dummy_functions: list[Function],
    dummy_api_key: str,
) -> None:
    # private functions should not be reachable for project with only public access
    crud.functions.set_function_visibility(db_session, dummy_functions[0].id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]
    assert len(functions) == len(dummy_functions) - 1

    # private functions should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]
    assert len(functions) == len(dummy_functions)

    # revert changes
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    crud.functions.set_function_visibility(db_session, dummy_functions[0].id, Visibility.PUBLIC)
    db_session.commit()


def test_list_functions_with_private_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_project: Project,
    dummy_functions: list[Function],
    dummy_api_key: str,
) -> None:
    # all functions (public and private) under private apps should not be reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_functions[0].app_id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]

    private_functions_count = sum(
        function.app_id == dummy_functions[0].app_id for function in dummy_functions
    )
    assert private_functions_count > 0, "there should be at least one private function"
    assert (
        len(functions) == len(dummy_functions) - private_functions_count
    ), "all functions under private apps should not be returned"

    # all functions (public and private) under private apps should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/", params={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [FunctionDetails.model_validate(func) for func in response.json()]
    assert len(functions) == len(dummy_functions)

    # revert changes
    crud.apps.set_app_visibility(db_session, dummy_functions[0].app_id, Visibility.PUBLIC)
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    db_session.commit()
