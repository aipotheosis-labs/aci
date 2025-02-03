from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import User
from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.agent import (
    AgentCreate,
    AgentPublic,
    CustomInstructionsCreate,
)
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
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_user_bearer_token: str,
) -> None:
    body = CustomInstructionsCreate(
        app_id=dummy_app_google.id,
        instructions="test instructions",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}/custom-instructions/",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    # get agent from db
    db_session.refresh(dummy_agent_1)
    agent = db_session.execute(
        select(Agent).filter(Agent.id == dummy_agent_1.id)
    ).scalar_one_or_none()
    assert agent is not None
    assert agent.custom_instructions.get(str(dummy_app_google.id)) == body.instructions


def test_create_two_custom_instructions(
    test_client: TestClient,
    db_session: Session,
    dummy_agent_1: Agent,
    dummy_app_google: App,
    dummy_app_github: App,
    dummy_user_bearer_token: str,
) -> None:
    body_1 = CustomInstructionsCreate(
        app_id=dummy_app_google.id,
        instructions="test instructions 1",
    )
    body_2 = CustomInstructionsCreate(
        app_id=dummy_app_github.id,
        instructions="test instructions 2",
    )
    response_1 = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}/custom-instructions/",
        json=body_1.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response_1.status_code == status.HTTP_200_OK
    response_2 = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}/agents/{dummy_agent_1.id}/custom-instructions/",
        json=body_2.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response_2.status_code == status.HTTP_200_OK
    db_session.refresh(dummy_agent_1)
    agent = db_session.execute(
        select(Agent).filter(Agent.id == dummy_agent_1.id)
    ).scalar_one_or_none()
    assert agent is not None
    assert agent.custom_instructions.get(str(dummy_app_google.id)) == body_1.instructions
    assert agent.custom_instructions.get(str(dummy_app_github.id)) == body_2.instructions
