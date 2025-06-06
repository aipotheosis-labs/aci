from fastapi import status
from fastapi.testclient import TestClient
from pytest_subtests import SubTests
from sqlalchemy.orm import Session

from aci.common import encryption
from aci.common.db import crud
from aci.common.db.sql_models import Agent, App, Function, LinkedAccount, Plan
from aci.common.enums import SecurityScheme
from aci.common.schemas.app_connectors.agent_secrets_manager import SecretValue
from aci.common.schemas.function import FunctionExecute, FunctionExecutionResult
from aci.common.schemas.secret import SecretCreate
from aci.common.schemas.security_scheme import NoAuthSchemeCredentials
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


def test_secrets_are_deleted_when_linked_account_is_deleted(
    test_client: TestClient,
    dummy_app_agent_secrets_manager: App,
    dummy_agent_1_with_all_apps_allowed: Agent,
    db_session: Session,
) -> None:
    """Test that secrets are automatically deleted when their parent linked account is deleted."""
    # Given: create a linked account for agent secrets manager
    linked_account = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_agent_1_with_all_apps_allowed.project_id,
        dummy_app_agent_secrets_manager.name,
        "test_secrets_cascading_deletion_owner",
        SecurityScheme.NO_AUTH,
        NoAuthSchemeCredentials(),
        enabled=True,
    )
    db_session.commit()

    # Given: create some secrets associated with the linked account
    secret_create_1 = SecretCreate(
        key="example.com",
        value=b"encrypted_credential_data_1",
    )
    secret_1 = crud.secret.create_secret(
        db_session,
        linked_account.id,
        secret_create_1,
    )

    secret_create_2 = SecretCreate(
        key="github.com",
        value=b"encrypted_credential_data_2",
    )

    secret_2 = crud.secret.create_secret(
        db_session,
        linked_account.id,
        secret_create_2,
    )
    db_session.commit()

    # Given: verify secrets exist before deletion
    secrets_before = crud.secret.list_secrets(db_session, linked_account.id)
    assert len(secrets_before) == 2, "Should have 2 secrets before deletion"

    # When: delete the linked account via API
    delete_response = test_client.delete(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{linked_account.id}",
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Then: verify linked account is deleted from DB
    deleted_linked_account = crud.linked_accounts.get_linked_account_by_id_under_project(
        db_session, linked_account.id, dummy_agent_1_with_all_apps_allowed.project_id
    )
    assert deleted_linked_account is None, "Linked account should be deleted from database"

    # Then: verify secrets are also deleted from DB (cascade delete)
    secrets_after = crud.secret.list_secrets(db_session, linked_account.id)
    assert len(secrets_after) == 0, "All secrets should be deleted when linked account is deleted"

    # Then: verify individual secrets are gone
    secret_1_after = crud.secret.get_secret(db_session, linked_account.id, secret_1.key)
    secret_2_after = crud.secret.get_secret(db_session, linked_account.id, secret_2.key)
    assert secret_1_after is None, "Secret 1 should be deleted"
    assert secret_2_after is None, "Secret 2 should be deleted"


def test_quota_enforcement_prevents_exceeding_credential_limit(
    test_client: TestClient,
    dummy_linked_account_no_auth_agent_secrets_manager_project_1: LinkedAccount,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_agent_secrets_manager__create_credential_for_domain: Function,
    dummy_function_agent_secrets_manager__list_credentials: Function,
    free_plan: Plan,
    db_session: Session,
) -> None:
    """Test that the system prevents creating more credentials than the quota allows."""
    # The free plan allows 5 agent credentials
    max_credentials = free_plan.features["agent_credentials"]

    # Use CRUD operations to populate credentials up to the quota limit
    for i in range(max_credentials):
        # Create properly encrypted secret value in the same format as the agent secrets manager
        secret_value = SecretValue(username=f"testuser{i}", password=f"testpassw0rd{i}!")
        encrypted_value = encryption.encrypt(secret_value.model_dump_json().encode())

        secret_create = SecretCreate(
            key=f"example{i}.com",
            value=encrypted_value,
        )
        crud.secret.create_secret(
            db_session,
            dummy_linked_account_no_auth_agent_secrets_manager_project_1.id,
            secret_create,
        )
    db_session.commit()

    # Verify we have created the maximum number of credentials using the list API
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
    assert function_execution_response.data is not None
    assert len(function_execution_response.data) == max_credentials

    # Now attempt to create one more credential via API, which should fail due to quota limit
    excess_credential = {
        "domain": "excess.com",
        "username": "excessuser",
        "password": "excesspassw0rd!",
    }

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_no_auth_agent_secrets_manager_project_1.linked_account_owner_id,
        function_input=excess_credential,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_agent_secrets_manager__create_credential_for_domain.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    # The request should fail with a 403 Forbidden status due to quota exceeded
    assert response.status_code == status.HTTP_200_OK
    function_execution_response = FunctionExecutionResult.model_validate(response.json())
    assert not function_execution_response.success
    assert function_execution_response.error is not None
    assert function_execution_response.error.startswith("Max agent secrets reached")

    # Verify that the number of credentials hasn't increased using CRUD
    secrets_after_failed_attempt = crud.secret.list_secrets(
        db_session, dummy_linked_account_no_auth_agent_secrets_manager_project_1.id
    )
    assert (
        len(secrets_after_failed_attempt) == max_credentials
    )  # Should still be at the limit, not exceeded
