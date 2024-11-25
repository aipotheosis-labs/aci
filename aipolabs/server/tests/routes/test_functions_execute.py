import json
from urllib.parse import parse_qs, urlparse

import responses
from fastapi.testclient import TestClient
from requests import PreparedRequest

from aipolabs.common.schemas.function import FunctionExecutionResult

AIPOLABS_TEST__HELLO_WORLD_WITH_ARGS = "AIPOLABS_TEST__HELLO_WORLD_WITH_ARGS"
AIPOLABS_TEST__HELLO_WORLD_NESTED_ARGS = "AIPOLABS_TEST__HELLO_WORLD_NESTED_ARGS"
AIPOLABS_TEST__HELLO_WORLD_NO_ARGS = "AIPOLABS_TEST__HELLO_WORLD_NO_ARGS"
AIPOLABS_TEST_HTTP_BEARER__HELLO_WORLD = "AIPOLABS_TEST_HTTP_BEARER__HELLO_WORLD"


def test_execute_function_with_invalid_input(test_client: TestClient, dummy_api_key: str) -> None:
    function_name = AIPOLABS_TEST__HELLO_WORLD_WITH_ARGS
    body = {"function_input": {"name": "John"}}
    response = test_client.post(
        f"/v1/functions/{function_name}/execute", json=body, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 400, response.json()


@responses.activate
def test_mock_execute_function_with_no_args(test_client: TestClient, dummy_api_key: str) -> None:
    # Mock the HTTP endpoint
    response_data = {"message": "Hello, test_mock_execute_function_with_no_args!"}
    responses.add(
        responses.GET,
        "https://api.mock.aipolabs.com/v1/hello_world_no_args",
        json=response_data,
        status=200,
    )

    function_name = AIPOLABS_TEST__HELLO_WORLD_NO_ARGS
    response = test_client.post(
        f"/v1/functions/{function_name}/execute", json={}, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == response_data


@responses.activate
def test_execute_function_with_args(test_client: TestClient, dummy_api_key: str) -> None:
    # Mock the HTTP endpoint
    mock_response_data = {"message": "Hello, test_execute_function_with_args!"}

    # Create a callback to verify request details
    def request_callback(request: PreparedRequest) -> tuple[int, dict, str]:
        # Parse URL to verify components separately
        parsed_url = urlparse(request.url)
        query_params = parse_qs(parsed_url.query)

        # Verify base URL and path
        assert (
            f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            == "https://api.mock.aipolabs.com/v1/greet/John"
        )

        # Verify query parameters
        assert query_params == {"lang": ["en"]}

        # Verify body, default greeting should be injected
        assert request.body == b'{"name": "John", "greeting": "default-greeting"}'

        # Verify headers
        assert request.headers["X-CUSTOM-HEADER"] == "header123"
        # verify default api key is injected
        assert request.headers["X-Test-API-Key"] == "test-api-key"

        # Verify cookie should not exist because default is null
        assert "Cookie" not in request.headers

        return (200, {}, json.dumps(mock_response_data))

    responses.add_callback(
        method=responses.POST,
        url="https://api.mock.aipolabs.com/v1/greet/John",
        callback=request_callback,
    )

    function_name = AIPOLABS_TEST__HELLO_WORLD_WITH_ARGS
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
        f"/v1/functions/{function_name}/execute",
        json=function_execution_request_body,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == mock_response_data


@responses.activate
def test_execute_function_with_nested_args(test_client: TestClient, dummy_api_key: str) -> None:
    # Mock the HTTP endpoint
    mock_response_data = {"message": "Hello, test_execute_function_with_args!"}

    # Create a callback to verify request details
    def request_callback(request: PreparedRequest) -> tuple[int, dict, str]:
        # Parse URL to verify components separately
        parsed_url = urlparse(request.url)
        query_params = parse_qs(parsed_url.query)

        # Verify base URL and path
        assert (
            f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            == "https://api.mock.aipolabs.com/v1/greet/John"
        )

        # verify default api key is injected
        assert request.headers["X-Test-API-Key"] == "test-api-key"

        # Verify default query parameters is injected
        assert query_params == {"lang": ["en"]}

        # Verify body have correct user input and default values are injected for non-visible properties
        assert (
            request.body
            == b'{"person": {"name": "John", "title": "default-title"}, "location": {"city": "New York", "country": "USA"}, "greeting": "default-greeting"}'
        )

        return (200, {}, json.dumps(mock_response_data))

    responses.add_callback(
        method=responses.POST,
        url="https://api.mock.aipolabs.com/v1/greet/John",
        callback=request_callback,
    )

    function_name = AIPOLABS_TEST__HELLO_WORLD_NESTED_ARGS
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
        f"/v1/functions/{function_name}/execute",
        json=function_execution_request_body,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == mock_response_data


@responses.activate
def test_http_bearer_auth_token_injection(test_client: TestClient, dummy_api_key: str) -> None:

    def request_callback(request: PreparedRequest) -> tuple[int, dict, str]:
        # Verify Bearer token is injected
        assert request.headers["Authorization"] == "Bearer test-bearer-token"

        return (200, {}, json.dumps({}))

    responses.add_callback(
        method=responses.GET,
        url="https://api.mock.aipolabs.com/v1/hello_world",
        callback=request_callback,
    )

    response = test_client.post(
        f"/v1/functions/{AIPOLABS_TEST_HTTP_BEARER__HELLO_WORLD}/execute",
        json={},
        headers={"x-api-key": dummy_api_key},
    )

    assert response.status_code == 200, response.json()
