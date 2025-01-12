import httpx
import respx
from fastapi import status
from fastapi.testclient import TestClient

from aipolabs.common.db.sql_models import Function
from aipolabs.common.schemas.function import FunctionExecutionResult
from aipolabs.server import config


def test_execute_function_with_invalid_input(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_function_aipolabs_test__hello_world_with_args: Function,
) -> None:
    body = {"function_input": {"name": "John"}}
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_with_args.id}/execute",
        json=body,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@respx.mock
def test_mock_execute_function_with_no_args(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_function_aipolabs_test__hello_world_no_args: Function,
) -> None:
    # Mock the HTTP endpoint
    response_data = {"message": "Hello, test_mock_execute_function_with_no_args!"}
    respx.get("https://api.mock.aipolabs.com/v1/hello_world_no_args").mock(
        return_value=httpx.Response(200, json=response_data)
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_no_args.id}/execute",
        json={},
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == response_data


@respx.mock
def test_execute_function_with_args(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_function_aipolabs_test__hello_world_with_args: Function,
) -> None:
    # Mock the HTTP endpoint
    mock_response_data = {"message": "Hello, test_execute_function_with_args!"}

    # Define the mock request and response
    request = respx.post("https://api.mock.aipolabs.com/v1/greet/John").mock(
        return_value=httpx.Response(
            200,
            json=mock_response_data,
            headers={"X-CUSTOM-HEADER": "header123", "X-Test-API-Key": "test-api-key"},
        )
    )

    function_execution_request_body = {
        "function_input": {
            "path": {"userId": "John"},
            "query": {"lang": "en"},
            "body": {"name": "John"},  # greeting is not visible so no input here
            "header": {"X-CUSTOM-HEADER": "header123"},
            # "cookie" property is not visible in our test schema so no input here
        }
    }
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_with_args.id}/execute",
        json=function_execution_request_body,
        headers={"x-api-key": dummy_api_key},
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
def test_execute_function_with_nested_args(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_function_aipolabs_test__hello_world_nested_args: Function,
) -> None:
    # Mock the HTTP endpoint
    mock_response_data = {"message": "Hello, test_execute_function_with_args!"}

    # Define the mock request and response
    request = respx.post("https://api.mock.aipolabs.com/v1/greet/John").mock(
        return_value=httpx.Response(
            200,
            json=mock_response_data,
            headers={"X-Test-API-Key": "test-api-key"},
        )
    )

    function_execution_request_body = {
        "function_input": {
            "path": {"userId": "John"},
            # "query": {"lang": "en"}, query is not visible so no input here
            "body": {
                "person": {"name": "John"},  # "title" is not visible so no input here
                # "greeting": "Hello", greeting is not visible so no input here
                "location": {"city": "New York", "country": "USA"},
            },
        }
    }
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__hello_world_nested_args.id}/execute",
        json=function_execution_request_body,
        headers={"x-api-key": dummy_api_key},
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


@respx.mock
def test_http_bearer_auth_token_injection(
    test_client: TestClient,
    dummy_api_key: str,
    dummy_function_aipolabs_test__http_bearer__hello_world: Function,
) -> None:
    # Mock the HTTP endpoint
    request = respx.get("https://api.mock.aipolabs.com/v1/hello_world").mock(
        return_value=httpx.Response(200, json={})
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aipolabs_test__http_bearer__hello_world.id}/execute",
        json={},
        headers={"x-api-key": dummy_api_key},
    )

    # Verify the request was made as expected
    assert request.called
    assert request.calls.last.request.headers["Authorization"] == "Bearer test-bearer-token"
    assert response.status_code == status.HTTP_200_OK
