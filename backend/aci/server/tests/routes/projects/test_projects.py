import uuid
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import App, Project
from aci.common.enums import SecurityScheme, Visibility
from aci.common.schemas.app_configurations import AppConfigurationCreate
from aci.common.schemas.project import ProjectCreate, ProjectPublic
from aci.common.schemas.security_scheme import NoAuthSchemeCredentials
from aci.server import billing, config
from aci.server.tests.conftest import DummyUser


def test_get_projects_success(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # Get the plan's project limit
    subscription = billing.get_subscription_by_org_id(db_session, dummy_user.org_id)
    max_projects = subscription.plan.features["projects"]

    # First create multiple projects
    for i in range(max_projects):
        project = crud.projects.create_project(db_session, dummy_user.org_id, f"project_{i}")
        db_session.commit()
        assert project is not None

    # Test getting all projects
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_200_OK
    public_projects = [ProjectPublic.model_validate(project) for project in response.json()]
    assert len(public_projects) == max_projects
    for public_project in public_projects:
        assert public_project.name in [f"project_{i}" for i in range(max_projects)]
        assert public_project.org_id == dummy_user.org_id


def test_get_projects_invalid_org_id(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            config.ACI_ORG_ID_HEADER: str(uuid.uuid4()),
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
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_project_reached_max_projects_per_org(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
) -> None:
    # Get the plan's project limit
    subscription = billing.get_subscription_by_org_id(db_session, dummy_user.org_id)
    max_projects = subscription.plan.features["projects"]

    # create max number of projects under the user
    for i in range(max_projects):
        project = crud.projects.create_project(db_session, dummy_user.org_id, f"project_{i}")
        db_session.commit()
        assert project is not None, f"should be able to create {max_projects} projects"

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
    dummy_user: DummyUser,
    dummy_project_1: Project,
) -> None:
    # Test updating the project
    update_body = {"name": "updated_project_name"}
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}",
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
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_project_empty_name(
    test_client: TestClient,
    dummy_user: DummyUser,
    dummy_project_1: Project,
) -> None:
    # Test updating with invalid data
    update_body = {"name": ""}  # Empty name should be invalid
    response = test_client.patch(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}",
        json=update_body,
        headers={"Authorization": f"Bearer {dummy_user.access_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_project_success(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
    dummy_project_1: Project,
) -> None:
    # Create a project using CRUD
    project = crud.projects.create_project(
        db_session,
        dummy_user.org_id,
        "project_test_delete",
    )
    db_session.commit()
    assert project is not None
    project_id = project.id

    # Test deleting one project (should succeed as it's not the last one)
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{project_id}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify project is deleted by getting all projects for the org
    projects = crud.projects.get_projects_by_org(db_session, dummy_user.org_id)
    assert len(projects) == 1
    assert projects[0].id == dummy_project_1.id


def test_delete_last_project(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
    dummy_project_1: Project,
) -> None:
    # Try to delete the last project (should fail)
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{dummy_project_1.id}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    # Verify project still exists using CRUD
    projects = crud.projects.get_projects_by_org(db_session, dummy_user.org_id)
    assert len(projects) == 1
    assert projects[0].id == dummy_project_1.id


def test_delete_project_not_found(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{uuid4()}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures(
    "dummy_project_1"
)  # Can't delete last project that's why we need this fixture
def test_delete_project_cascading_deletion(
    test_client: TestClient,
    dummy_user: DummyUser,
    dummy_apps: list[App],
    db_session: Session,
) -> None:
    dummy_app = dummy_apps[0]
    # First create a project using CRUD
    project = crud.projects.create_project(
        db_session,
        dummy_user.org_id,
        "project_test_cascading_deletion",
    )
    db_session.commit()
    project_id = project.id

    app_config_body = AppConfigurationCreate(
        app_name=dummy_app.name,
        security_scheme=SecurityScheme.NO_AUTH,
    )

    # Create an app configuration using CRUD
    crud.app_configurations.create_app_configuration(
        db_session,
        project_id,
        app_config_body,
    )
    db_session.commit()

    # Create a linked account using CRUD
    crud.linked_accounts.create_linked_account(
        db_session,
        project_id,
        dummy_app.name,
        "test_link_no_auth_account_success",
        SecurityScheme.NO_AUTH,
        NoAuthSchemeCredentials(),
        enabled=True,
    )
    db_session.commit()

    # Create an agent using CRUD
    crud.projects.create_agent(
        db_session,
        project_id,
        "new test agent",
        "new test agent description",
        allowed_apps=[dummy_app.name],
        custom_instructions={},
    )
    db_session.commit()

    # Delete the project
    delete_response = test_client.delete(
        f"{config.ROUTER_PREFIX_PROJECTS}/{project_id}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify app configuration is deleted from DB
    deleted_app_config = crud.app_configurations.get_app_configuration(
        db_session, project_id, dummy_app.name
    )
    assert deleted_app_config is None, "App configuration should be deleted from database"

    # Verify linked account is deleted from DB
    deleted_linked_account = crud.linked_accounts.get_linked_account(
        db_session, project_id, dummy_app.name, "test_link_no_auth_account_success"
    )
    assert deleted_linked_account is None, "Linked account should be deleted from database"

    # Verify agent is deleted from DB
    deleted_agent = crud.projects.get_agents_by_project(db_session, project_id)
    assert len(deleted_agent) == 0, "Agent should be deleted from database"


def test_cannot_access_project_from_other_org(
    test_client: TestClient,
    db_session: Session,
    dummy_user: DummyUser,
    dummy_user_2: DummyUser,
) -> None:
    # Create a project for dummy_user_2
    crud.projects.create_project(
        db_session,
        org_id=dummy_user_2.org_id,
        name="Other Org Project",
    )
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_PROJECTS}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_200_OK
    projects = response.json()
    assert len(projects) == 0, "User should not see projects from other organizations"
