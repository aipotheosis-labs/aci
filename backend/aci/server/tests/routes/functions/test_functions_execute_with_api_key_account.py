import json

import httpx
import pytest
import respx
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db.sql_models import Agent, App, Function, LinkedAccount
from aci.common.enums import SecurityScheme
from aci.common.schemas.function import FunctionExecute, FunctionExecutionResult
from aci.common.schemas.security_scheme import APIKeySchemeCredentials
from aci.server import config


@respx.mock
@pytest.mark.parametrize(
    "header_token_prefix",
    ["Bearer", None],
)
def test_execute_function_with_linked_account_api_key(
    db_session: Session,
    test_client: TestClient,
    header_token_prefix: str | None,
    dummy_app_aci_test: App,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_aci_test__hello_world_no_args: Function,
    dummy_linked_account_api_key_aci_test_project_1: LinkedAccount,
) -> None:
    """
    Test that the function is executed with the end-user's linked account API key
    """
    # Reset the API key scheme prefix to cover both cases: with and without prefix
    # Note: nested update is not supported (won't trigger the onupdate event) in SQLAlchemy, so we need to do it this way
    api_key_scheme = dummy_app_aci_test.security_schemes[SecurityScheme.API_KEY].copy()
    api_key_scheme["prefix"] = header_token_prefix
    dummy_app_aci_test.security_schemes[SecurityScheme.API_KEY] = api_key_scheme
    db_session.commit()

    response_data = {"message": "Hello, test_mock_execute_function_with_no_args!"}
    mock_request = respx.get("https://api.mock.aci.com/v1/hello_world_no_args").mock(
        return_value=httpx.Response(200, json=response_data)
    )

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_api_key_aci_test_project_1.linked_account_owner_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == response_data
    assert mock_request.called, "Request should be made"

    linked_account_api_key = APIKeySchemeCredentials.model_validate(
        dummy_linked_account_api_key_aci_test_project_1.security_credentials
    )
    if header_token_prefix:
        assert (
            mock_request.calls.last.request.headers["X-Test-API-Key"]
            == f"{header_token_prefix} {linked_account_api_key.secret_key}"
        )
    else:
        assert (
            mock_request.calls.last.request.headers["X-Test-API-Key"]
            == linked_account_api_key.secret_key
        )


@respx.mock
@pytest.mark.parametrize(
    "function_fixture, function_input, expected_url, expected_content, expected_response_data",
    [
        # No args test case
        (
            "dummy_function_aci_test__hello_world_no_args",
            None,
            "https://api.mock.aci.com/v1/hello_world_no_args",
            None,
            {"message": "Hello, test_mock_execute_function_with_no_args!"},
        ),
        # With args test case
        (
            "dummy_function_aci_test__hello_world_with_args",
            {
                "path": {"userId": "John"},
                "query": {"lang": "en"},
                "body": {"name": "John"},  # greeting is not visible so no input here
                "header": {"X-CUSTOM-HEADER": "header123"},
                # "cookie" property is not visible in our test schema so no input here
            },
            "https://api.mock.aci.com/v1/greet/John?lang=en",
            b'{"name": "John", "greeting": "default-greeting"}',
            {"message": "Hello, test_execute_api_key_based_function_with_args!"},
        ),
        # Nested args test case
        (
            "dummy_function_aci_test__hello_world_nested_args",
            {
                "path": {"userId": "John"},
                # "query": {"lang": "en"}, query is not visible so no input here
                "body": {
                    "person": {"name": "John"},  # "title" is not visible so no input here
                    # "greeting": "Hello", greeting is not visible so no input here
                    "location": {"city": "New York", "country": "USA"},
                },
            },
            "https://api.mock.aci.com/v1/greet/John?lang=en",
            b'{"person": {"name": "John", "title": "default-title"}, '
            b'"location": {"city": "New York", "country": "USA"}, '
            b'"greeting": "default-greeting"}',
            {"message": "Hello, test_execute_api_key_based_function_with_nested_args!"},
        ),
    ],
)
def test_execute_function_with_app_default_api_key(
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    function_fixture: str,
    function_input: dict,
    expected_url: str,
    expected_content: bytes,
    expected_response_data: dict,
    dummy_linked_account_default_api_key_aci_test_project_1: LinkedAccount,
    request: pytest.FixtureRequest,
) -> None:
    # Get the actual function fixture
    function = request.getfixturevalue(function_fixture)

    # Mock the HTTP endpoint
    if "no_args" in function_fixture:
        # For no_args case, use GET request
        mock_request = respx.get(expected_url).mock(
            return_value=httpx.Response(200, json=expected_response_data)
        )
    else:
        # For cases with args, use POST request
        mock_request = respx.post(expected_url).mock(
            return_value=httpx.Response(200, json=expected_response_data)
        )

    # Prepare function execution request
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aci_test_project_1.linked_account_owner_id,
    )
    if function_input:
        function_execute.function_input = function_input

    # Execute the function
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{function.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == expected_response_data

    # Verify the request was made as expected
    assert mock_request.called
    assert mock_request.calls.last.request.url == expected_url

    # Check API key header for cases with args
    if "no_args" not in function_fixture:
        assert (
            mock_request.calls.last.request.headers["X-Test-API-Key"] == "default-shared-api-key"
        ), "API key used should be default-shared-api-key set for the App"

        # Check for custom header in the with_args test case
        if function_input and "X-CUSTOM-HEADER" in function_input.get("header", {}):
            assert mock_request.calls.last.request.headers["X-CUSTOM-HEADER"] == "header123"

        # Verify request content for cases with args
        assert json.loads(mock_request.calls.last.request.content) == json.loads(expected_content)
