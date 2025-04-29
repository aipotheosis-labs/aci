import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db.sql_models import Agent, AppConfiguration, Function, LinkedAccount
from aci.common.schemas.function import FunctionExecute
from aci.server import config

NON_EXISTENT_FUNCTION_NAME = "non_existent_function_name"
NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID = "dummy_linked_account_owner_id"


def test_execute_non_existent_function(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_default_api_key_aci_test_project_1: LinkedAccount,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aci_test_project_1.linked_account_owner_id,
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
    dummy_function_aci_test__hello_world_no_args: Function,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")


def test_execute_function_whose_app_configuration_is_disabled(
    db_session: Session,
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_function_aci_test__hello_world_no_args: Function,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfiguration,
) -> None:
    dummy_app_configuration_api_key_aci_test_project_1.enabled = False
    db_session.commit()

    function_execute = FunctionExecute(
        linked_account_owner_id=NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(response.json()["error"]).startswith("App configuration disabled")


def test_execute_function_linked_account_not_found(
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_aci_test__hello_world_no_args: Function,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfiguration,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=NON_EXISTENT_LINKED_ACCOUNT_OWNER_ID,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("Linked account not found")


def test_execute_function_linked_account_disabled(
    db_session: Session,
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_aci_test__hello_world_no_args: Function,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfiguration,
    dummy_linked_account_default_api_key_aci_test_project_1: LinkedAccount,
) -> None:
    dummy_linked_account_default_api_key_aci_test_project_1.enabled = False
    db_session.commit()

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aci_test_project_1.linked_account_owner_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert str(response.json()["error"]).startswith("Linked account disabled")


def test_execute_function_with_invalid_function_input(
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_aci_test__hello_world_with_args: Function,
    dummy_linked_account_default_api_key_aci_test_project_1: LinkedAccount,
) -> None:
    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aci_test_project_1.linked_account_owner_id,
        function_input={"path": {"random_key": "random_value"}},
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_with_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert str(response.json()["error"]).startswith("Invalid function input")


@pytest.mark.parametrize("allow_agent_to_access_app", [True, False])
def test_execute_function_of_app_that_is_not_allowed_for_agent(
    db_session: Session,
    test_client: TestClient,
    dummy_agent_1_with_no_apps_allowed: Agent,
    allow_agent_to_access_app: bool,
    dummy_function_aci_test__hello_world_no_args: Function,
    dummy_linked_account_default_api_key_aci_test_project_1: LinkedAccount,
) -> None:
    if allow_agent_to_access_app:
        dummy_agent_1_with_no_apps_allowed.allowed_apps = [
            dummy_function_aci_test__hello_world_no_args.app.name
        ]
        db_session.commit()

    function_execute = FunctionExecute(
        linked_account_owner_id=dummy_linked_account_default_api_key_aci_test_project_1.linked_account_owner_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    if allow_agent_to_access_app:
        assert response.status_code == status.HTTP_200_OK
    else:
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert str(response.json()["error"]).startswith("App not allowed for this agent")
