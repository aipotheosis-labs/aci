from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import Agent, APIKey, Project, User
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
    assert response.status_code == 200, response.json()
    project_public = ProjectPublic.model_validate(response.json())
    assert project_public.name == body.name
    assert project_public.owner_id == dummy_user.id
    assert project_public.visibility_access == Visibility.PUBLIC

    # Verify the project was actually created in the database and values match returned values
    db_project = crud.projects.get_project(db_session, project_public.id)

    assert db_project is not None
    assert project_public.model_dump() == ProjectPublic.model_validate(db_project).model_dump()


def test_create_agent(
    test_client: TestClient,
    db_session: Session,
    dummy_project: Project,
    dummy_user_bearer_token: str,
) -> None:
    body = AgentCreate(
        name="new test agent",
        description="new test agent description",
    )

    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project.id}/agents/",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == 200, response.json()
    agent_public = AgentPublic.model_validate(response.json())
    assert agent_public.name == body.name
    assert agent_public.description == body.description
    assert agent_public.project_id == dummy_project.id

    # Verify the agent was actually created in the database and values match returned values
    db_agent = db_session.execute(
        select(Agent).filter(Agent.id == agent_public.id)
    ).scalar_one_or_none()

    assert db_agent is not None
    assert agent_public.model_dump() == AgentPublic.model_validate(db_agent).model_dump()

    # check api keys
    db_api_key = db_session.execute(
        select(APIKey).filter(APIKey.agent_id == db_agent.id)
    ).scalar_one_or_none()
    assert db_api_key is not None
    assert len(agent_public.api_keys) == 1
    assert agent_public.api_keys[0].key == db_api_key.key

    # Clean up: no need to delete agent and api key, it will be deleted when dummy_project is deleted
