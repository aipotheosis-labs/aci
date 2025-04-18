import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import Agent, Function, LinkedAccount
from aci.common.schemas.function import FunctionExecute, FunctionExecutionResult
from aci.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aci.server import config


@pytest.mark.parametrize(
    "function_input, expected_response_data",
    [
        (
            {
                "input_string": "test_string",
                "input_int": 1,
                "input_bool": True,
                "input_list": ["test_string1", "test_string2"],
            },
            {
                "input_string": "test_string",
                "input_int": 1,
                "input_bool": True,
                "input_list": ["test_string1", "test_string2"],
                "input_required_invisible_string": "default_string_value",
                "security_scheme": "no_auth",
                "security_scheme_cls": NoAuthScheme.__name__,
                "security_credentials_cls": NoAuthSchemeCredentials.__name__,
            },
        ),
    ],
)
def test_execute_echo(
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_mock_app_connector__echo: Function,
    dummy_linked_account_no_auth_mock_app_connector_project_1: LinkedAccount,
    function_input: dict,
    expected_response_data: dict,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_no_auth_mock_app_connector_project_1.linked_account_owner_id,
        function_input=function_input,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_mock_app_connector__echo.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    assert response.status_code == status.HTTP_200_OK
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert function_execution_response.success
    assert function_execution_response.data == expected_response_data


def test_execute_fail(
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_mock_app_connector__fail: Function,
    dummy_linked_account_no_auth_mock_app_connector_project_1: LinkedAccount,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_no_auth_mock_app_connector_project_1.linked_account_owner_id,
        function_input={},
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_mock_app_connector__fail.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    assert response.status_code == status.HTTP_200_OK
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert not function_execution_response.success, "function should fail"
