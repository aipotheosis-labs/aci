import httpx
import respx
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import (
    Agent,
    AppConfiguration,
    Function,
    LinkedAccount,
)
from aipolabs.common.schemas.function import FunctionExecute, FunctionExecutionResult
from aipolabs.server import config

NON_EXISTENT_FUNCTION_NAME = "non_existent_function_name"
NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID = "dummy_linked_account_owner_id"


def test_execute_non_existent_function(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_default_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aipolabs_test_project_1.linked_account_owner_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{NON_EXISTENT_FUNCTION_NAME}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("Function not found")


# Note that if no app configuration or linkedin account is injected to test as fixture,
# the app will not be configured.
def test_execute_function_whose_app_is_not_configured(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_no_args: Function,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")


def test_execute_function_whose_app_configuration_is_disabled(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_no_args: Function,
    dummy_app_configuration_api_key_aipolabs_test_project_1: AppConfiguration,
) -> None:
    dummy_app_configuration_api_key_aipolabs_test_project_1.enabled = False
    db_session.commit()

    function_execute = FunctionExecute(
        linked_account_owner_id=NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(response.json()["error"]).startswith("App configuration disabled")


def test_execute_function_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_no_args: Function,
    dummy_app_configuration_api_key_aipolabs_test_project_1: AppConfiguration,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("Linked account not found")


def test_execute_function_linked_account_disabled(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_no_args: Function,
    dummy_app_configuration_api_key_aipolabs_test_project_1: AppConfiguration,
    dummy_linked_account_default_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    dummy_linked_account_default_api_key_aipolabs_test_project_1.enabled = False
    db_session.commit()

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aipolabs_test_project_1.linked_account_owner_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(response.json()["error"]).startswith("Linked account disabled")


def test_execute_function_with_invalid_function_input(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_with_args: Function,
    dummy_linked_account_default_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aipolabs_test_project_1.linked_account_owner_id,
        function_input={"path": {"random_key": "random_value"}},
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_with_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert str(response.json()["error"]).startswith("Invalid function input")


@respx.mock
def test_execute_function_with_custom_instructions_success(
    test_client: TestClient,
    dummy_agent_with_github_apple_instructions: Agent,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
    dummy_function_github__create_repository: Function,
) -> None:
    # TODO: change needed here when we abstract out to InferenceService
    # Allow real calls to OpenAI API
    respx.post("https://api.openai.com/v1/chat/completions").pass_through()

    # Mock only the GitHub API endpoint
    mock_response_data = {"id": 123, "name": "test-repo"}
    github_request = respx.post("https://api.github.com/repositories").mock(
        return_value=httpx.Response(201, json=mock_response_data)
    )

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_github_project_1.linked_account_owner_id,
        function_input={
            "body": {
                "name": "test-repo",  # Note: not using "apple" in name so it passes the filter
                "description": "Test repository",
                "private": True,
            }
        },
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_with_github_apple_instructions.api_keys[0].key},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == mock_response_data

    # Verify the GitHub request was made as expected
    assert github_request.called
    assert github_request.calls.last.request.url == "https://api.github.com/repositories"
    assert (
        github_request.calls.last.request.content
        == b'{"name": "test-repo", "description": "Test repository", "private": true}'
    )


def test_execute_function_with_custom_instructions_rejected(
    test_client: TestClient,
    dummy_agent_with_github_apple_instructions: Agent,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
    dummy_function_github__create_repository: Function,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_github_project_1.linked_account_owner_id,
        function_input={
            "body": {
                "name": "apple-test-repo",
                "description": "Test repository",
                "private": True,
            }
        },
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_with_github_apple_instructions.api_keys[0].key},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    apple_custom_instructions = dummy_agent_with_github_apple_instructions.custom_instructions[
        dummy_function_github__create_repository.app.name
    ]
    assert apple_custom_instructions in response.json()["error"]
