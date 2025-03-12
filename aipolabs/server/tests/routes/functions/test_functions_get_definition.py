from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Function, Project
from aipolabs.common.enums import FunctionDefinitionFormat, Visibility
from aipolabs.common.schemas.function import (
    AnthropicFunctionDefinition,
    OpenAIFunctionDefinition,
)
from aipolabs.server import config


def test_get_function_definition_openai_by_identifier(
    test_client: TestClient,
    dummy_function_github__create_repository: Function,
    dummy_api_key_1: str,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.name}/definition",
        params={"format": FunctionDefinitionFormat.OPENAI},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    function_definition = OpenAIFunctionDefinition.model_validate(response_json)
    assert function_definition.type == "function"
    assert function_definition.function.name == dummy_function_github__create_repository.name
    # Sanity check: ensure that the description is the same
    assert (
        function_definition.function.description
        == dummy_function_github__create_repository.description
    )


def test_get_function_definition_anthropic_by_identifier(
    test_client: TestClient,
    dummy_function_github__create_repository: Function,
    dummy_api_key_1: str,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.name}/definition",
        params={"format": FunctionDefinitionFormat.ANTHROPIC},
        headers={"x-api-key": dummy_api_key_1},
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
    dummy_api_key_1: str,
    dummy_project_1: Project,
) -> None:
    # private function should not be reachable for project with only public access
    crud.functions.set_function_visibility(db_session, dummy_functions[0].name, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].name}/definition",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].name}/definition",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_function_that_is_under_private_app(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    dummy_project_1: Project,
) -> None:
    # public function under private app should not be reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_functions[0].app.name, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].name}/definition",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].name}/definition",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_function_that_is_inactive(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
) -> None:
    # inactive function should not be reachable
    crud.functions.set_function_active_status(db_session, dummy_functions[0].name, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].name}/definition",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_function_that_is_under_inactive_app(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
) -> None:
    # functions (active or inactive) under inactive app should not be reachable
    crud.apps.set_app_active_status(db_session, dummy_functions[0].app.name, False)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_functions[0].name}/definition",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
