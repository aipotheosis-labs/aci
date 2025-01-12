from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Function, Project
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.function import (
    AnthropicFunctionDefinition,
    OpenAIFunctionDefinition,
)
from aipolabs.server import config


def test_get_function_definition_openai(
    test_client: TestClient,
    dummy_function_github__create_repository: Function,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.id}/definition",
        params={"inference_provider": "openai"},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    function_definition = OpenAIFunctionDefinition.model_validate(response_json)
    assert function_definition.type == "function"
    assert function_definition.function.name == dummy_function_github__create_repository.name
    # sanity check: if description is the same
    assert (
        function_definition.function.description
        == dummy_function_github__create_repository.description
    )


def test_get_function_definition_anthropic(
    test_client: TestClient,
    dummy_function_github__create_repository: Function,
    dummy_api_key: str,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.id}/definition",
        params={"inference_provider": "anthropic"},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    function_definition = AnthropicFunctionDefinition.model_validate(response.json())
    assert function_definition.name == dummy_function_github__create_repository.name
    # sanity check: if description is the same
    assert function_definition.description == dummy_function_github__create_repository.description


def test_get_private_function(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key: str,
    dummy_project: Project,
) -> None:
    # private function should not be reachable for project with only public access
    crud.functions.set_function_visibility(db_session, dummy_functions[0].id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].id}/definition",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].id}/definition",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK

    # revert changes
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    crud.functions.set_function_visibility(db_session, dummy_functions[0].id, Visibility.PUBLIC)
    db_session.commit()


def test_get_function_that_is_under_private_app(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key: str,
    dummy_project: Project,
) -> None:
    # public function under private app should not be reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_functions[0].app_id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].id}/definition",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].id}/definition",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK

    # revert changes
    crud.apps.set_app_visibility(db_session, dummy_functions[0].app_id, Visibility.PUBLIC)
    crud.projects.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    db_session.commit()


def test_get_function_that_is_disabled(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key: str,
) -> None:
    # disabled function should not be reachable
    crud.functions.set_function_enabled_status(db_session, dummy_functions[0].id, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].id}/definition",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # revert changes
    crud.functions.set_function_enabled_status(db_session, dummy_functions[0].id, True)
    db_session.commit()


def test_get_function_that_is_under_disabled_app(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key: str,
) -> None:
    # functions (public or private) under disabled app should not be reachable
    crud.apps.set_app_enabled_status(db_session, dummy_functions[0].app_id, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].id}/definition",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # revert changes
    crud.apps.set_app_enabled_status(db_session, dummy_functions[0].app_id, True)
    db_session.commit()
