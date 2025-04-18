import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Function, Project
from aci.common.enums import FunctionDefinitionFormat, Visibility
from aci.common.schemas.function import (
    AnthropicFunctionDefinition,
    BasicFunctionDefinition,
    OpenAIFunctionDefinition,
)
from aci.server import config


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_get_function_definition_by_identifier(
    test_client: TestClient,
    dummy_function_github__create_repository: Function,
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.name}/definition",
        params={"format": format},
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    function_definition: (
        BasicFunctionDefinition | OpenAIFunctionDefinition | AnthropicFunctionDefinition
    )
    match format:
        case FunctionDefinitionFormat.BASIC:
            function_definition = BasicFunctionDefinition.model_validate(response_json)
            assert function_definition.name == dummy_function_github__create_repository.name
            assert (
                function_definition.description
                == dummy_function_github__create_repository.description
            )
        case FunctionDefinitionFormat.OPENAI:
            function_definition = OpenAIFunctionDefinition.model_validate(response_json)
            assert function_definition.type == "function"
            assert (
                function_definition.function.name == dummy_function_github__create_repository.name
            )
            assert (
                function_definition.function.description
                == dummy_function_github__create_repository.description
            )
        case FunctionDefinitionFormat.ANTHROPIC:
            function_definition = AnthropicFunctionDefinition.model_validate(response_json)
            assert function_definition.name == dummy_function_github__create_repository.name
            assert (
                function_definition.description
                == dummy_function_github__create_repository.description
            )


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
