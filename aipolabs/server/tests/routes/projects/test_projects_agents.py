from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Agent, APIKey, App, Project
from aipolabs.common.schemas.agent import AgentCreate, AgentPublic, AgentUpdate
from aipolabs.server import config


def test_create_agent(
    test_client: TestClient,
    db_session: Session,
    dummy_project_1: Project,
    dummy_user_bearer_token: str,
) -> None:
    body = AgentCreate(
        name="new test agent",
        description="new test agent description",
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.name == body.name
    assert agent_public.description == body.description
    assert agent_public.project_id == dummy_project_1.id

    # Verify the agent was actually created in the database and values match returned values
    agent = db_session.execute(
        select(Agent).filter(Agent.id == agent_public.id)
    ).scalar_one_or_none()

    assert agent is not None
    assert agent_public.model_dump() == AgentPublic.model_validate(agent).model_dump()

    # check api keys
    api_key = db_session.execute(
        select(APIKey).filter(APIKey.agent_id == agent.id)
    ).scalar_one_or_none()
    assert api_key is not None
    assert len(agent_public.api_keys) == 1
    assert agent_public.api_keys[0].key == api_key.key


def test_update_agent(
    test_client: TestClient,
    db_session: Session,
    dummy_project_1: Project,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_app_github: App,
    dummy_user_bearer_token: str,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{dummy_agent_1.id}"

    # Test updating name and description
    response = test_client.patch(
        ENDPOINT,
        json={"name": "Updated Agent Name", "description": "Updated description"},
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.name == "Updated Agent Name"
    assert agent_public.description == "Updated description"

    # Test updating excluded apps and functions
    response = test_client.patch(
        ENDPOINT,
        json={
            "excluded_apps": [dummy_app_google.name],
            "excluded_functions": [],
        },
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert dummy_app_google.name in agent_public.excluded_apps
    assert len(agent_public.excluded_functions) == 0

    # Test updating custom instructions
    body = AgentUpdate(
        custom_instructions={dummy_app_github.name: "Custom GitHub instructions"},
    )
    response = test_client.patch(
        ENDPOINT,
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.custom_instructions == {dummy_app_github.name: "Custom GitHub instructions"}

    # Test updating only name preserves other fields
    previous_state = agent_public.model_dump()
    response = test_client.patch(
        ENDPOINT,
        json={"name": "Final Name Update"},
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())

    # Verify name changed but everything else stayed the same
    assert agent_public.name == "Final Name Update"
    assert agent_public.description == previous_state["description"]
    assert agent_public.excluded_apps == previous_state["excluded_apps"]
    assert agent_public.excluded_functions == previous_state["excluded_functions"]
    assert agent_public.custom_instructions == previous_state["custom_instructions"]


def test_update_agent_multiple_custom_instructions(
    test_client: TestClient,
    db_session: Session,
    dummy_project_1: Project,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_app_github: App,
    dummy_user_bearer_token: str,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{dummy_agent_1.id}"

    # Add first custom instruction for Google app
    body = AgentUpdate(
        custom_instructions={dummy_app_google.name: "Custom Google instructions"},
    )
    response = test_client.patch(
        ENDPOINT,
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.custom_instructions == {dummy_app_google.name: "Custom Google instructions"}

    # Add second custom instruction for GitHub app while preserving Google app instruction
    body = AgentUpdate(
        custom_instructions={
            dummy_app_google.name: "Custom Google instructions",
            dummy_app_github.name: "Custom GitHub instructions",
        },
    )
    response = test_client.patch(
        ENDPOINT,
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.custom_instructions == {
        dummy_app_google.name: "Custom Google instructions",
        dummy_app_github.name: "Custom GitHub instructions",
    }


def test_update_agent_nonexistent_agent(
    test_client: TestClient,
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_google: App,
    dummy_user_bearer_token: str,
) -> None:
    """Test that attempting to create custom instructions for a nonexistent agent returns 404"""
    # Generate a random UUID that doesn't exist in the database
    nonexistent_agent_id = uuid4()
    body = AgentUpdate(
        custom_instructions={dummy_app_google.name: "Custom Google instructions"},
    )
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{nonexistent_agent_id}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_agent_unauthorized_user(
    test_client: TestClient,
    db_session: Session,
    dummy_project_1: Project,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_user_2_bearer_token: str,  # Need to add this fixture
) -> None:
    """Test that unauthorized users cannot update custom instructions"""
    body = AgentUpdate(
        custom_instructions={dummy_app_google.name: "Custom Google instructions"},
    )
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{dummy_agent_1.id}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_2_bearer_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_agent_custom_instructions_restrictions(
    test_client: TestClient,
    db_session: Session,
    dummy_project_1: Project,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_user_bearer_token: str,
) -> None:
    """Test that custom instructions cannot be empty strings"""
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{dummy_agent_1.id}",
        json={"custom_instructions": {str(dummy_app_google.id): ""}},
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Verify valid instructions still work
    body = AgentUpdate(
        custom_instructions={dummy_app_google.name: "Valid instructions"},
    )
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{dummy_agent_1.id}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["custom_instructions"][dummy_app_google.name] == "Valid instructions"


def test_delete_agent(
    test_client: TestClient,
    db_session: Session,
    dummy_project_1: Project,
    dummy_agent_1: Agent,
    dummy_user_bearer_token: str,
) -> None:
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{dummy_agent_1.id}",
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    agent = crud.projects.get_agent_by_id(db_session, dummy_agent_1.id)
    assert agent is None, "agent should be deleted"

    api_key = crud.projects.get_api_key_by_agent_id(db_session, dummy_agent_1.id)
    assert api_key is None, "api key associated with agent should be deleted"


def test_delete_agent_not_found(
    test_client: TestClient,
    dummy_project_1: Project,
    dummy_user_bearer_token: str,
) -> None:
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/{uuid4()}",
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_agent_unauthorized(
    test_client: TestClient,
    dummy_project_2: Project,
    dummy_user_2_bearer_token: str,
    dummy_agent_1: Agent,
) -> None:
    """
    user2 with access to dummy_project_2 should not be able to delete dummy_agent_1 (belongs to dummy_project_1)
    """
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_2.id}/agents/{dummy_agent_1.id}",
        headers={"Authorization": f"Bearer {dummy_user_2_bearer_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
