from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud, sql_models
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.function import (
    AnthropicFunctionDefinition,
    OpenAIFunctionDefinition,
)

GOOGLE__CALENDAR_CREATE_EVENT = "GOOGLE__CALENDAR_CREATE_EVENT"
GITHUB__CREATE_REPOSITORY = "GITHUB__CREATE_REPOSITORY"
GITHUB = "GITHUB"
GOOGLE = "GOOGLE"


def test_get_function_definition_openai(
    test_client: TestClient, dummy_functions: list[sql_models.Function], dummy_api_key: str
) -> None:
    function_name = GITHUB__CREATE_REPOSITORY
    response = test_client.get(
        f"/v1/functions/{function_name}/definition",
        params={"inference_provider": "openai"},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    response_json = response.json()

    function_definition = OpenAIFunctionDefinition.model_validate(response_json)
    assert function_definition.type == "function"
    assert function_definition.function.name == function_name
    # sanity check: if description is the same
    dummy_function = next(
        function for function in dummy_functions if function.name == function_name
    )
    assert function_definition.function.description == dummy_function.description


def test_get_function_definition_anthropic(
    test_client: TestClient, dummy_functions: list[sql_models.Function], dummy_api_key: str
) -> None:
    function_name = GOOGLE__CALENDAR_CREATE_EVENT
    response = test_client.get(
        f"/v1/functions/{function_name}/definition",
        params={"inference_provider": "anthropic"},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    function_definition = AnthropicFunctionDefinition.model_validate(response.json())
    assert function_definition.name == function_name
    # sanity check: if description is the same
    dummy_function = next(
        function for function in dummy_functions if function.name == function_name
    )
    assert function_definition.description == dummy_function.description


def test_get_private_function(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
    dummy_project: sql_models.Project,
) -> None:
    # private function should not be reachable for project with only public access
    crud.set_function_visibility(db_session, dummy_functions[0].id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"/v1/functions/{dummy_functions[0].name}/definition",
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 404, response.json()

    # should be reachable for project with private access
    crud.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"/v1/functions/{dummy_functions[0].name}/definition", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()

    # revert changes
    crud.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    crud.set_function_visibility(db_session, dummy_functions[0].id, Visibility.PUBLIC)
    db_session.commit()


def test_get_function_that_is_under_private_app(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
    dummy_project: sql_models.Project,
) -> None:
    # public function under private app should not be reachable for project with only public access
    crud.set_app_visibility(db_session, dummy_functions[0].app_id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"/v1/functions/{dummy_functions[0].name}/definition", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 404, response.json()

    # should be reachable for project with private access
    crud.set_project_visibility_access(db_session, dummy_project.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"/v1/functions/{dummy_functions[0].name}/definition", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()

    # revert changes
    crud.set_app_visibility(db_session, dummy_functions[0].app_id, Visibility.PUBLIC)
    crud.set_project_visibility_access(db_session, dummy_project.id, Visibility.PUBLIC)
    db_session.commit()


def test_get_function_that_is_disabled(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    # disabled function should not be reachable
    crud.set_function_enabled_status(db_session, dummy_functions[0].id, False)
    db_session.commit()

    response = test_client.get(
        f"/v1/functions/{dummy_functions[0].name}/definition", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 404, response.json()

    # revert changes
    crud.set_function_enabled_status(db_session, dummy_functions[0].id, True)
    db_session.commit()


def test_get_function_that_is_under_disabled_app(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    # functions (public or private) under disabled app should not be reachable
    crud.set_app_enabled_status(db_session, dummy_functions[0].app_id, False)
    db_session.commit()

    response = test_client.get(
        f"/v1/functions/{dummy_functions[0].name}/definition", headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 404, response.json()

    # revert changes
    crud.set_app_enabled_status(db_session, dummy_functions[0].app_id, True)
    db_session.commit()
