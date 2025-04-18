from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.common.schemas.linked_accounts import LinkedAccountNoAuthCreate
from aci.common.schemas.security_scheme import NoAuthSchemeCredentials
from aci.server import config


def test_link_no_auth_account(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_no_auth_mock_app_connector_project_1: AppConfigurationPublic,
    db_session: Session,
) -> None:
    body = LinkedAccountNoAuthCreate(
        app_name=dummy_linked_account_no_auth_mock_app_connector_project_1.app_name,
        linked_account_owner_id="test_link_no_auth_account_success",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=body.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK

    # expire the session to get the latest data
    db_session.expire_all()

    linked_account_db = crud.linked_accounts.get_linked_account(
        db_session,
        dummy_linked_account_no_auth_mock_app_connector_project_1.project_id,
        dummy_linked_account_no_auth_mock_app_connector_project_1.app_name,
        body.linked_account_owner_id,
    )
    assert linked_account_db is not None
    NoAuthSchemeCredentials.model_validate(linked_account_db.security_credentials)

    # linking the same account again should fail
    # TODO: update this if later we support updating existing api_key linked accounts
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=body.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_link_no_auth_account_under_non_no_auth_app_configuration_should_fail(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_mock_app_connector_project_1: AppConfigurationPublic,
) -> None:
    body = LinkedAccountNoAuthCreate(
        app_name=dummy_linked_account_oauth2_mock_app_connector_project_1.app_name,
        linked_account_owner_id="test_link_no_auth_account_under_non_no_auth_app_configuration",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=body.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert str(response.json()["error"]).startswith("No implementation found")
