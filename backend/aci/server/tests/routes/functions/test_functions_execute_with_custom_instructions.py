import httpx
import pytest
import respx
from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import Agent, Function, LinkedAccount
from aci.common.schemas.agent import AgentUpdate
from aci.common.schemas.function import FunctionExecute
from aci.server import config
from aci.server.tests.conftest import DummyUser


@pytest.mark.parametrize(
    ("custom_instruction", "repo_name", "function_execution_should_succeed"),
    [
        ("", "stupid repo", True),
        ("abc 123", "stupid repo", True),
        ("you can create repo with any name", "stupid repo", True),
        ("you can NOT create repo with an offensive name", "stupid repo", False),
        ("you can NOT create repo with an offensive name", "good repo", True),
    ],
)
@respx.mock
def test_execute_github_function_with_custom_instructions(
    test_client: TestClient,
    dummy_user: DummyUser,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_function_github__create_repository: Function,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
    custom_instruction: str,
    repo_name: str,
    function_execution_should_succeed: bool,
) -> None:
    # let the openai request pass through
    respx.post("https://api.openai.com/v1/chat/completions").pass_through()
    # mock the github request
    mock_response_data = {"repo_name": repo_name}
    github_request = respx.post("https://api.github.com/repositories").mock(
        return_value=httpx.Response(201, json=mock_response_data)
    )

    function_input = {
        "body": {
            "name": repo_name,
            "description": "this is a github repo",
            "private": True,
        }
    }

    # update the agent with custom instructions if non empty string
    if custom_instruction:
        agent_update = AgentUpdate(
            custom_instructions={dummy_function_github__create_repository.name: custom_instruction}
        )
        agent_update_response = test_client.patch(
            f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_agent_1_with_all_apps_allowed.project_id}/agents/{dummy_agent_1_with_all_apps_allowed.id}",
            json=agent_update.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {dummy_user.access_token}"},
        )
        assert agent_update_response.status_code == status.HTTP_200_OK

    # execute the function
    response = test_client.post(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_github__create_repository.name}/execute",
        json=FunctionExecute(
            linked_account_owner_id=dummy_linked_account_api_key_github_project_1.linked_account_owner_id,
            function_input=function_input,
        ).model_dump(mode="json"),
        headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
    )

    if function_execution_should_succeed:
        assert github_request.called
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == {"repo_name": repo_name}
        assert response.json()["success"]
    else:
        assert not github_request.called
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert str(response.json()["error"]).startswith("Custom instruction violation")
        assert custom_instruction in str(response.json()["error"])
