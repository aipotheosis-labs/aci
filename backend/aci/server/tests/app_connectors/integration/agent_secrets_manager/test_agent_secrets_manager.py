from fastapi import status
from fastapi.testclient import TestClient
from pytest_subtests import SubTests

from aci.common.db.sql_models import Agent, Function, LinkedAccount
from aci.common.schemas.function import FunctionExecute, FunctionExecutionResult
from aci.server import config


def test_credentials_workflow(
    test_client: TestClient,
    dummy_linked_account_no_auth_agent_secrets_manager_project_1: LinkedAccount,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_agent_secrets_manager__list_credentials: Function,
    dummy_function_agent_secrets_manager__create_credential_for_domain: Function,
    dummy_function_agent_secrets_manager__get_credential_for_domain: Function,
    dummy_function_agent_secrets_manager__update_credential_for_domain: Function,
    dummy_function_agent_secrets_manager__delete_credential_for_domain: Function,
    subtests: SubTests,
) -> None:
    with subtests.test("list credentials - no credentials initially"):
        function_execute = FunctionExecute(
            linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
            function_input={},
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__list_credentials.name}/execute",
            json=function_execute.model_dump(mode="json"),
            headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
        )

        assert response.status_code == status.HTTP_200_OK
        function_execution_response = FunctionExecutionResult.model_validate(response.json())
        assert function_execution_response.success
        assert function_execution_response.data == []

    with subtests.test("create credential for domain"):
        user_domain_credential = {
            "domain": "aci.dev",
            "username": "testuser",
            "password": "testpassw0rd!",
        }

        function_execute = FunctionExecute(
            linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
            function_input=user_domain_credential,
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__create_credential_for_domain.name}/execute",
            json=function_execute.model_dump(mode="json"),
            headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
        )

        assert response.status_code == status.HTTP_200_OK
        function_execution_response = FunctionExecutionResult.model_validate(response.json())
        assert function_execution_response.success
        assert function_execution_response.data is None

    with subtests.test("list credentials - one credential"):
        function_execute = FunctionExecute(
            linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
            function_input={},
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__list_credentials.name}/execute",
            json=function_execute.model_dump(mode="json"),
            headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
        )

        assert response.status_code == status.HTTP_200_OK
        function_execution_response = FunctionExecutionResult.model_validate(response.json())
        assert function_execution_response.success
        assert function_execution_response.data == [user_domain_credential]

    with subtests.test("get credential for domain"):
        function_execute = FunctionExecute(
            linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
            function_input={"domain": user_domain_credential["domain"]},
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__get_credential_for_domain.name}/execute",
            json=function_execute.model_dump(mode="json"),
            headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
        )

        assert response.status_code == status.HTTP_200_OK
        function_execution_response = FunctionExecutionResult.model_validate(response.json())
        assert function_execution_response.success
        assert function_execution_response.data == user_domain_credential

    with subtests.test("update credential for domain"):
        updated_user_domain_credential = {
            "domain": user_domain_credential["domain"],
            "username": user_domain_credential["username"],
            "password": "newpassw0rd!",
        }

        function_execute = FunctionExecute(
            linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
            function_input=updated_user_domain_credential,
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__update_credential_for_domain.name}/execute",
            json=function_execute.model_dump(mode="json"),
            headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
        )

        assert response.status_code == status.HTTP_200_OK
        function_execution_response = FunctionExecutionResult.model_validate(response.json())
        assert function_execution_response.success
        assert function_execution_response.data is None

    with subtests.test("delete credential for domain"):
        function_execute = FunctionExecute(
            linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
            function_input={"domain": user_domain_credential["domain"]},
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__delete_credential_for_domain.name}/execute",
            json=function_execute.model_dump(mode="json"),
            headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
        )

        assert response.status_code == status.HTTP_200_OK
        function_execution_response = FunctionExecutionResult.model_validate(response.json())
        assert function_execution_response.success
        assert function_execution_response.data is None

    with subtests.test("list credentials - no credentials after deletion"):
        function_execute = FunctionExecute(
            linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
            function_input={},
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__list_credentials.name}/execute",
            json=function_execute.model_dump(mode="json"),
            headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
        )

        assert response.status_code == status.HTTP_200_OK
        function_execution_response = FunctionExecutionResult.model_validate(response.json())
        assert function_execution_response.success
        assert function_execution_response.data == []
