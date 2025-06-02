from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Agent, App, LinkedAccount
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.server import config


def test_delete_app_configuration(
    db_session: Session,
    test_client: TestClient,
    dummy_agent_1_with_all_apps_allowed: Agent,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/"
        f"{dummy_app_configuration_oauth2_google_project_1.app_name}"
    )
    project_id = dummy_app_configuration_oauth2_google_project_1.project_id
    app_name = dummy_app_configuration_oauth2_google_project_1.app_name
    linked_account_owner_id = dummy_linked_account_oauth2_google_project_1.linked_account_owner_id

    # pre-delete state checks
    linked_account = crud.linked_accounts.get_linked_account(
        db_session, project_id, app_name, linked_account_owner_id
    )
    assert linked_account is not None, (
        "linked account should exist before deleting the app configuration"
    )
    assert app_name in dummy_agent_1_with_all_apps_allowed.allowed_apps, (
        "app should in the agent's allowed apps list"
    )

    response = test_client.delete(
        ENDPOINT, headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key}
    )
    assert response.status_code == status.HTTP_200_OK

    # get deleted app configuration should return 404
    response = test_client.get(
        ENDPOINT, headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")

    # expire all to get fresh data
    db_session.expire_all()

    # post-delete state checks
    linked_account = crud.linked_accounts.get_linked_account(
        db_session, project_id, app_name, linked_account_owner_id
    )
    assert linked_account is None, "linked account should be deleted"
    updated_agent = crud.projects.get_agent_by_id(
        db_session, dummy_agent_1_with_all_apps_allowed.id
    )
    assert updated_agent is not None, "agent should exist"
    assert app_name not in updated_agent.allowed_apps, (
        "app should no longer be in the agent's allowed apps list"
    )


def test_delete_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aci_test: App,
) -> None:
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_APP_CONFIGURATIONS}/{dummy_app_aci_test.name}",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")
