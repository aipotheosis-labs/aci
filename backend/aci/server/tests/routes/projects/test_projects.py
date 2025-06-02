from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.enums import Visibility
from aci.common.schemas.agent import AgentCreate, AgentPublic
from aci.common.schemas.project import ProjectCreate, ProjectPublic
from aci.server import config
from aci.server.tests.conftest import DummyUser


def test_create_project_under_user(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    body = ProjectCreate(
        name="project_test_create_project_under_user",
        org_id=dummy_user.org_id,
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    project_public = ProjectPublic.model_validate(response.json())
    assert project_public.name == body.name
    assert project_public.org_id == dummy_user.org_id
    assert project_public.visibility_access == Visibility.PUBLIC

    # Verify the project was actually created in the database and values match returned values
    project = crud.projects.get_project(db_session, project_public.id)

    assert project is not None
    assert project_public.model_dump() == ProjectPublic.model_validate(project).model_dump()


def test_create_project_reached_max_projects_per_org(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    # create max number of projects under the user
    for i in range(config.MAX_PROJECTS_PER_ORG):
        body = ProjectCreate(name=f"project_{i}", org_id=dummy_user.org_id)
        response = test_client.post(
            f"{config.ROUTER_PREFIX_PROJECTS}",
            json=body.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {dummy_user.access_token}"},
        )
        assert response.status_code == status.HTTP_200_OK, (
            f"should be able to create {config.MAX_PROJECTS_PER_ORG} projects"
        )

    # try to create one more project under the user
    body = ProjectCreate(name=f"project_{config.MAX_PROJECTS_PER_ORG}", org_id=dummy_user.org_id)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_projects_under_user(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # create projects and agents under the user
    number_of_projects = 3
    number_of_agents_per_project = 2
    for i in range(number_of_projects):
        body = ProjectCreate(name=f"project_{i}", org_id=dummy_user.org_id)
        response = test_client.post(
            f"{config.ROUTER_PREFIX_PROJECTS}",
            json=body.model_dump(mode="json"),
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_200_OK
        project_public = ProjectPublic.model_validate(response.json())

        for j in range(number_of_agents_per_project):
            body = AgentCreate(  # type: ignore
                name=f"project_{i}_agent_{j}",
                description=f"project_{i}_agent_{j} description",
            )
            response = test_client.post(
                f"{config.ROUTER_PREFIX_PROJECTS}/{project_public.id}/agents",
                json=body.model_dump(mode="json"),
                headers={
                    "Authorization": f"Bearer {dummy_user.access_token}",
                    "X-ACI-ORG-ID": str(dummy_user.org_id),
                },
            )
            assert response.status_code == status.HTTP_200_OK

    # get projects under the user
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_200_OK
    projects_public = [ProjectPublic.model_validate(project) for project in response.json()]
    assert len(projects_public) == number_of_projects
    for project in projects_public:
        agents_public = [AgentPublic.model_validate(agent) for agent in project.agents]
        assert len(agents_public) == number_of_agents_per_project
        for agent in agents_public:
            assert len(agent.api_keys) == 1, "each agent should have one api key"
