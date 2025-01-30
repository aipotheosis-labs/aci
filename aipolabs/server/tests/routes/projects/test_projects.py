from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Agent, APIKey, App, Project, User
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.agent import AgentCreate, AgentPublic
from aipolabs.common.schemas.project import ProjectCreate, ProjectPublic
from aipolabs.server import config


def test_create_project_under_user(
    test_client: TestClient,
    db_session: Session,
    dummy_user_bearer_token: str,
    dummy_user: User,
) -> None:
    body = ProjectCreate(name="project_test_create_project_under_user")
    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}/",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    project_public = ProjectPublic.model_validate(response.json())
    assert project_public.name == body.name
    assert project_public.owner_id == dummy_user.id
    assert project_public.visibility_access == Visibility.PUBLIC

    # Verify the project was actually created in the database and values match returned values
    project = crud.projects.get_project(db_session, project_public.id)

    assert project is not None
    assert project_public.model_dump() == ProjectPublic.model_validate(project).model_dump()


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
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}/agents/",
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


def test_get_projects_under_user(
    test_client: TestClient, db_session: Session, dummy_user_bearer_token: str, dummy_user: User
) -> None:
    # create projects and agents under the user
    number_of_projects = 3
    number_of_agents_per_project = 2
    for i in range(number_of_projects):
        body = ProjectCreate(name=f"project_{i}")
        response = test_client.post(
            f"{config.ROUTER_PREFIX_PROJECTS}/",
            json=body.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        project_public = ProjectPublic.model_validate(response.json())

        for j in range(number_of_agents_per_project):
            body = AgentCreate(
                name=f"project_{i}_agent_{j}", description=f"project_{i}_agent_{j} description"
            )
            response = test_client.post(
                f"{config.ROUTER_PREFIX_PROJECTS}/{project_public.id}/agents/",
                json=body.model_dump(mode="json"),
                headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
            )
            assert response.status_code == status.HTTP_200_OK

    # get projects under the user
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}/",
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    projects_public = [ProjectPublic.model_validate(project) for project in response.json()]
    assert len(projects_public) == number_of_projects
    for project in projects_public:
        agents_public = [AgentPublic.model_validate(agent) for agent in project.agents]
        assert len(agents_public) == number_of_agents_per_project
        for agent in agents_public:
            assert len(agent.api_keys) == 1, "each agent should have one api key"


def test_create_custom_instructions(
    test_client: TestClient,
    db_session: Session,
    dummy_user: User,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_user_bearer_token: str,
) -> None:

    ENDPOINT = f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}"
    response = test_client.patch(
        ENDPOINT,
        json={"custom_instructions": {str(dummy_app_google.id): "test instructions"}},
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.custom_instructions == {str(dummy_app_google.id): "test instructions"}


def test_update_agent(
    test_client: TestClient,
    db_session: Session,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_app_github: App,
    dummy_user_bearer_token: str,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}"

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
            "excluded_apps": [str(dummy_app_google.id)],
            "excluded_functions": [],
        },
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert dummy_app_google.id in agent_public.excluded_apps
    assert len(agent_public.excluded_functions) == 0

    # Test updating custom instructions
    response = test_client.patch(
        ENDPOINT,
        json={"custom_instructions": {str(dummy_app_github.id): "Custom GitHub instructions"}},
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.custom_instructions == {
        str(dummy_app_github.id): "Custom GitHub instructions"
    }


def test_update_multiple_custom_instructions(
    test_client: TestClient,
    db_session: Session,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_app_github: App,
    dummy_user_bearer_token: str,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}"

    # Add first custom instruction for Google app
    response = test_client.patch(
        ENDPOINT,
        json={"custom_instructions": {str(dummy_app_google.id): "Custom Google instructions"}},
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.custom_instructions == {
        str(dummy_app_google.id): "Custom Google instructions"
    }

    # Add second custom instruction for GitHub app while preserving Google app instruction
    response = test_client.patch(
        ENDPOINT,
        json={
            "custom_instructions": {
                str(dummy_app_google.id): "Custom Google instructions",
                str(dummy_app_github.id): "Custom GitHub instructions",
            }
        },
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.custom_instructions == {
        str(dummy_app_google.id): "Custom Google instructions",
        str(dummy_app_github.id): "Custom GitHub instructions",
    }


def test_create_custom_instructions_nonexistent_agent(
    test_client: TestClient,
    db_session: Session,
    dummy_app_google: App,
    dummy_user_bearer_token: str,
) -> None:
    """Test that attempting to create custom instructions for a nonexistent agent returns 404"""
    # Generate a random UUID that doesn't exist in the database
    nonexistent_agent_id = uuid4()

    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/agents/{nonexistent_agent_id}",
        json={
            "custom_instructions": {
                str(dummy_app_google.id): "Custom instructions for nonexistent agent"
            }
        },
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_custom_instructions_unauthorized_user(
    test_client: TestClient,
    db_session: Session,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_user_2_bearer_token: str,  # Need to add this fixture
) -> None:
    """Test that unauthorized users cannot update custom instructions"""
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}",
        json={
            "custom_instructions": {
                str(dummy_app_google.id): "Custom instructions from unauthorized user"
            }
        },
        headers={"Authorization": f"Bearer {dummy_user_2_bearer_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_custom_instructions_restrictions(
    test_client: TestClient,
    db_session: Session,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_user_bearer_token: str,
) -> None:
    """Test that custom instructions cannot be empty strings"""
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}",
        json={
            "custom_instructions": {str(dummy_app_google.id): ""}  # Empty string should be rejected
        },
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Verify valid instructions still work
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}",
        json={"custom_instructions": {str(dummy_app_google.id): "Valid instructions"}},
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["custom_instructions"][str(dummy_app_google.id)] == "Valid instructions"
