import uuid
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.enums import Visibility
from aci.common.schemas.project import ProjectCreate, ProjectPublic
from aci.server import config
from aci.server.tests.conftest import DummyUser


def test_get_projects_success(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # Get the plan's project limit
    plan = crud.subscriptions.get_plan_for_org(db_session, dummy_user.org_id)
    max_projects = plan.features.get("projects", 1)

    # First create multiple projects
    for i in range(max_projects):
        body = ProjectCreate(
            name=f"project_{i}",
            org_id=dummy_user.org_id,
        )
        create_response = test_client.post(
            f"{config.ROUTER_PREFIX_PROJECTS}",
            json=body.model_dump(mode="json"),
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert create_response.status_code == status.HTTP_200_OK

    # Test getting all projects
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_200_OK
    projects = [ProjectPublic.model_validate(project) for project in response.json()]
    assert len(projects) == max_projects
    for project in projects:
        assert project.name in [f"project_{i}" for i in range(max_projects)]
        assert project.org_id == dummy_user.org_id


def test_get_projects_invalid_org_id(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            "X-ACI-ORG-ID": str(uuid.uuid4()),
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_project(
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


def test_create_project_empty_name(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    # Send raw JSON data with empty name
    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        json={
            "name": "",
            "org_id": str(dummy_user.org_id),
        },
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_project_reached_max_projects_per_org(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # Get the plan's project limit
    plan = crud.subscriptions.get_plan_for_org(db_session, dummy_user.org_id)
    max_projects = plan.features.get("projects", 1)

    # create max number of projects under the user
    for i in range(max_projects):
        body = ProjectCreate(name=f"project_{i}", org_id=dummy_user.org_id)
        response = test_client.post(
            f"{config.ROUTER_PREFIX_PROJECTS}",
            json=body.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {dummy_user.access_token}"},
        )
        assert response.status_code == status.HTTP_200_OK, (
            f"should be able to create {max_projects} projects"
        )

    # try to create one more project under the user
    body = ProjectCreate(name=f"project_{max_projects}", org_id=dummy_user.org_id)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_project_success(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # First create a project
    body = ProjectCreate(
        name="project_test_update",
        org_id=dummy_user.org_id,
    )
    create_response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert create_response.status_code == status.HTTP_200_OK
    project_id = ProjectPublic.model_validate(create_response.json()).id

    # Test updating the project
    update_body = {"name": "updated_project_name"}
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{project_id}",
        json=update_body,
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    updated_project = ProjectPublic.model_validate(response.json())
    assert updated_project.name == update_body["name"]
    assert updated_project.org_id == dummy_user.org_id


def test_update_project_not_found(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    update_body = {"name": "updated_project_name"}
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{uuid4()}",
        json=update_body,
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_project_empty_name(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # First create a project
    body = ProjectCreate(
        name="project_test_update_invalid",
        org_id=dummy_user.org_id,
    )
    create_response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        json=body.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert create_response.status_code == status.HTTP_200_OK
    project_id = ProjectPublic.model_validate(create_response.json()).id

    # Test updating with invalid data
    update_body = {"name": ""}  # Empty name should be invalid
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{project_id}",
        json=update_body,
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_project_success(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # First create two projects
    project_names = ["project_1", "project_2"]
    project_ids = []
    for name in project_names:
        body = ProjectCreate(
            name=name,
            org_id=dummy_user.org_id,
        )
        create_response = test_client.post(
            f"{config.ROUTER_PREFIX_PROJECTS}",
            json=body.model_dump(mode="json"),
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert create_response.status_code == status.HTTP_200_OK
        project_ids.append(ProjectPublic.model_validate(create_response.json()).id)

    # Test deleting one project (should succeed as it's not the last one)
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{project_ids[0]}",
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify project is deleted
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_200_OK
    projects = [ProjectPublic.model_validate(project) for project in response.json()]
    assert len(projects) == 1
    assert projects[0].id == project_ids[1]


def test_delete_last_project(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # First create a project
    body = ProjectCreate(
        name="last_project",
        org_id=dummy_user.org_id,
    )
    create_response = test_client.post(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        json=body.model_dump(mode="json"),
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert create_response.status_code == status.HTTP_200_OK
    project_id = ProjectPublic.model_validate(create_response.json()).id

    # Try to delete the last project (should fail)
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{project_id}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    # Verify project still exists
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_200_OK
    projects = [ProjectPublic.model_validate(project) for project in response.json()]
    assert len(projects) == 1
    assert projects[0].id == project_id


def test_delete_project_not_found(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{uuid4()}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            "X-ACI-ORG-ID": str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
