import json

import httpx
import pytest
import respx
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Agent, Function, LinkedAccount
from aci.common.enums import SecurityScheme
from aci.common.schemas.function import FunctionExecute, FunctionExecutionResult
from aci.common.schemas.security_scheme import OAuth2Scheme, OAuth2SchemeCredentials
from aci.server import config


@respx.mock
@pytest.mark.parametrize("use_custom_oauth2_app", [True, False])
def test_execute_oauth2_based_function_with_linked_account_credentials(
    db_session: Session,
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_aci_test__hello_world_with_args: Function,
    dummy_linked_account_oauth2_aci_test_project_1: LinkedAccount,
    use_custom_oauth2_app: bool,
) -> None:
    # update the linked account's credentials if use_custom_oauth2_app is True
    if use_custom_oauth2_app:
        dummy_linked_account_oauth2_aci_test_project_1.security_credentials["client_id"] = (
            "custom_client_id"
        )
        dummy_linked_account_oauth2_aci_test_project_1.security_credentials["client_secret"] = (
            "custom_client_secret"
        )
        crud.linked_accounts.update_linked_account_credentials(
            db_session,
            dummy_linked_account_oauth2_aci_test_project_1,
            security_credentials=OAuth2SchemeCredentials.model_validate(
                dummy_linked_account_oauth2_aci_test_project_1.security_credentials
            ),
        )
        db_session.commit()

    # Mock the HTTP endpoint and response
    mock_response_data = {
        "message": "Hello, test_execute_oauth2_based_function_with_linked_account_credentials!"
    }
    request = respx.post("https://api.mock.aci.com/v1/greet/John").mock(
        return_value=httpx.Response(
            200,
            json=mock_response_data,
        )
    )

    # execute the function
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_oauth2_aci_test_project_1.linked_account_owner_id,
        function_input={
            "path": {"userId": "John"},
            "query": {"lang": "en"},
            "body": {"name": "John"},  # greeting is not visible so no input here
            "header": {"X-CUSTOM-HEADER": "header123"},
            # "cookie" property is not visible in our test schema so no input here
        },
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_with_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    # verify response is successful
    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == mock_response_data

    # Verify the request was made with correct inputs
    assert request.called
    assert request.calls.last.request.url == "https://api.mock.aci.com/v1/greet/John?lang=en"
    assert request.calls.last.request.headers["X-CUSTOM-HEADER"] == "header123"
    assert json.loads(request.calls.last.request.content) == json.loads(
        '{"name": "John","greeting": "default-greeting"}'
    )

    # verify request was made with the correct credentials
    # TODO: adding tests for scenarios where the access_token is placed in other location
    # (e.g., header, query, cookie). Might need to refactor the test cases and fixtures first to have a
    # more flexible and generic way of injecting different apps, functions, app_configurations, etc.
    app = dummy_function_aci_test__hello_world_with_args.app
    oauth2_scheme = OAuth2Scheme.model_validate(app.security_schemes[SecurityScheme.OAUTH2])
    linked_account_oauth2_credentials = OAuth2SchemeCredentials.model_validate(
        dummy_linked_account_oauth2_aci_test_project_1.security_credentials
    )
    assert (
        request.calls.last.request.headers["Authorization"]
        == f"{oauth2_scheme.prefix} {linked_account_oauth2_credentials.access_token}"
    )


@respx.mock
@pytest.mark.parametrize("use_custom_oauth2_app", [True, False])
def test_execute_oauth2_based_function_with_expired_linked_account_access_token(
    db_session: Session,
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_aci_test__hello_world_with_args: Function,
    dummy_linked_account_oauth2_aci_test_project_1: LinkedAccount,
    use_custom_oauth2_app: bool,
) -> None:
    # update the linked account's credentials if use_custom_oauth2_app is True
    if use_custom_oauth2_app:
        dummy_linked_account_oauth2_aci_test_project_1.security_credentials["client_id"] = (
            "custom_client_id"
        )
        dummy_linked_account_oauth2_aci_test_project_1.security_credentials["client_secret"] = (
            "custom_client_secret"
        )
        crud.linked_accounts.update_linked_account_credentials(
            db_session,
            dummy_linked_account_oauth2_aci_test_project_1,
            security_credentials=OAuth2SchemeCredentials.model_validate(
                dummy_linked_account_oauth2_aci_test_project_1.security_credentials
            ),
        )
        db_session.commit()

    # Mock the function's HTTP endpoint and response
    mock_response_data = {
        "message": "Hello, test_execute_oauth2_based_function_with_expired_linked_account_access_token!"
    }
    request = respx.post("https://api.mock.aci.com/v1/greet/John").mock(
        return_value=httpx.Response(
            200,
            json=mock_response_data,
        )
    )

    # mock the refresh token endpoint
    mock_refresh_token_response = {
        "access_token": "dummy_new_access_token",
        "expires_in": 3600,
    }
    respx.post("https://api.mock.aci.com/v1/oauth2/refresh").mock(
        return_value=httpx.Response(
            200,
            json=mock_refresh_token_response,
        )
    )

    # set the linked account's access token to expired
    linked_account_oauth2_credentials = OAuth2SchemeCredentials.model_validate(
        dummy_linked_account_oauth2_aci_test_project_1.security_credentials
    )
    old_access_token = linked_account_oauth2_credentials.access_token
    linked_account_oauth2_credentials.expires_at = 0
    crud.linked_accounts.update_linked_account_credentials(
        db_session,
        dummy_linked_account_oauth2_aci_test_project_1,
        security_credentials=linked_account_oauth2_credentials,
    )
    db_session.commit()

    # execute the function
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_oauth2_aci_test_project_1.linked_account_owner_id,
        function_input={
            "path": {"userId": "John"},
            "query": {"lang": "en"},
            "body": {"name": "John"},  # greeting is not visible so no input here
            "header": {"X-CUSTOM-HEADER": "header123"},
            # "cookie" property is not visible in our test schema so no input here
        },
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_with_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    # verify response is successful
    assert response.status_code == status.HTTP_200_OK
    assert "error" not in response.json()
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == mock_response_data

    # Verify the request was made with correct inputs
    assert request.called
    assert request.calls.last.request.url == "https://api.mock.aci.com/v1/greet/John?lang=en"
    assert request.calls.last.request.headers["X-CUSTOM-HEADER"] == "header123"
    assert json.loads(request.calls.last.request.content) == json.loads(
        '{"name": "John", "greeting": "default-greeting"}'
    )

    # verify request was made with the new access token
    app = dummy_function_aci_test__hello_world_with_args.app
    oauth2_scheme = OAuth2Scheme.model_validate(app.security_schemes[SecurityScheme.OAUTH2])
    assert (
        request.calls.last.request.headers["Authorization"]
        == f"{oauth2_scheme.prefix} {mock_refresh_token_response['access_token']}"
    )
    assert old_access_token != mock_refresh_token_response["access_token"]

    # verify the linked account's access token was updated
    db_session.refresh(dummy_linked_account_oauth2_aci_test_project_1)
    assert (
        dummy_linked_account_oauth2_aci_test_project_1.security_credentials["access_token"]
        == mock_refresh_token_response["access_token"]
    )
