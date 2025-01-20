import httpx
import respx
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import AppConfiguration, Function, LinkedAccount
from aipolabs.common.schemas.function import FunctionExecute, FunctionExecutionResult
from aipolabs.server import config

NON_EXISTENT_FUNCTION_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID = "dummy_linked_account_owner_id"


def test_execute_non_existent_function(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_aipolabs_test_project_1.linked_account_owner_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{NON_EXISTENT_FUNCTION_ID}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"] == "Function not found"


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
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"] == "App configuration not found"


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
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"] == "App configuration disabled"


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
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"] == "Linked account not found"


def test_execute_function_linked_account_disabled(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_no_args: Function,
    dummy_app_configuration_api_key_aipolabs_test_project_1: AppConfiguration,
    dummy_linked_account_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    dummy_linked_account_api_key_aipolabs_test_project_1.enabled = False
    db_session.commit()

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_aipolabs_test_project_1.linked_account_owner_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"] == "Linked account disabled"


def test_execute_function_with_invalid_function_input(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_with_args: Function,
    dummy_linked_account_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_aipolabs_test_project_1.linked_account_owner_id,
        function_input={"path": {"random_key": "random_value"}},
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_with_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "Invalid function input"


@respx.mock
def test_mock_execute_function_with_no_args(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_no_args: Function,
    dummy_linked_account_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    # Mock the HTTP endpoint
    response_data = {"message": "Hello, test_mock_execute_function_with_no_args!"}
    respx.get("https://api.mock.aipolabs.com/v1/hello_world_no_args").mock(
        return_value=httpx.Response(200, json=response_data)
    )

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_aipolabs_test_project_1.linked_account_owner_id,
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == response_data


@respx.mock
def test_execute_api_key_based_function_with_args(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_with_args: Function,
    dummy_linked_account_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    # Mock the HTTP endpoint
    mock_response_data = {"message": "Hello, test_execute_api_key_based_function_with_args!"}

    # Define the mock request and response
    request = respx.post("https://api.mock.aipolabs.com/v1/greet/John").mock(
        return_value=httpx.Response(
            200,
            json=mock_response_data,
            headers={"X-CUSTOM-HEADER": "header123", "X-Test-API-Key": "test-api-key"},
        )
    )

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_aipolabs_test_project_1.linked_account_owner_id,
        function_input={
            "path": {"userId": "John"},
            "query": {"lang": "en"},
            "body": {"name": "John"},  # greeting is not visible so no input here
            "header": {"X-CUSTOM-HEADER": "header123"},
            # "cookie" property is not visible in our test schema so no input here
        },
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_with_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == mock_response_data

    # Verify the request was made as expected
    assert request.called
    assert request.calls.last.request.url == "https://api.mock.aipolabs.com/v1/greet/John?lang=en"
    assert request.calls.last.request.headers["X-CUSTOM-HEADER"] == "header123"
    assert request.calls.last.request.headers["X-Test-API-Key"] == "test-api-key"
    assert request.calls.last.request.content == b'{"name": "John", "greeting": "default-greeting"}'


@respx.mock
def test_execute_api_key_based_function_with_nested_args(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aipolabs_test__hello_world_nested_args: Function,
    dummy_linked_account_api_key_aipolabs_test_project_1: LinkedAccount,
) -> None:
    # Mock the HTTP endpoint
    mock_response_data = {"message": "Hello, test_execute_api_key_based_function_with_nested_args!"}

    # Define the mock request and response
    request = respx.post("https://api.mock.aipolabs.com/v1/greet/John").mock(
        return_value=httpx.Response(
            200,
            json=mock_response_data,
            headers={"X-Test-API-Key": "test-api-key"},
        )
    )

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_aipolabs_test_project_1.linked_account_owner_id,
        function_input={
            "path": {"userId": "John"},
            # "query": {"lang": "en"}, query is not visible so no input here
            "body": {
                "person": {"name": "John"},  # "title" is not visible so no input here
                # "greeting": "Hello", greeting is not visible so no input here
                "location": {"city": "New York", "country": "USA"},
            },
        },
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_nested_args.id}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == mock_response_data

    # Verify the request was made as expected
    assert request.called
    assert request.calls.last.request.url == "https://api.mock.aipolabs.com/v1/greet/John?lang=en"
    assert request.calls.last.request.headers["X-Test-API-Key"] == "test-api-key"
    assert request.calls.last.request.content == (
        b'{"person": {"name": "John", "title": "default-title"}, '
        b'"location": {"city": "New York", "country": "USA"}, '
        b'"greeting": "default-greeting"}'
    )
