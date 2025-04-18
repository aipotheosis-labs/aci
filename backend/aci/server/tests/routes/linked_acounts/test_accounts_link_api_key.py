from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.common.schemas.linked_accounts import LinkedAccountAPIKeyCreate
from aci.common.schemas.security_scheme import APIKeySchemeCredentials
from aci.server import config

MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
)


def test_link_api_key_account(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
    db_session: Session,
) -> None:
    body = LinkedAccountAPIKeyCreate(
        app_name=dummy_app_configuration_api_key_github_project_1.app_name,
        linked_account_owner_id="test_link_api_key_account_success",
        api_key="test_linked_account_api_key",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=body.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK

    # expire the session to get the latest data
    db_session.expire_all()

    linked_account_db = crud.linked_accounts.get_linked_account(
        db_session,
        dummy_app_configuration_api_key_github_project_1.project_id,
        dummy_app_configuration_api_key_github_project_1.app_name,
        body.linked_account_owner_id,
    )
    assert linked_account_db is not None
    security_credentials = APIKeySchemeCredentials.model_validate(
        linked_account_db.security_credentials
    )
    assert security_credentials.secret_key == body.api_key

    # linking the same account again should fail
    # TODO: update this if later we support updating existing api_key linked accounts
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=body.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_link_api_key_account_under_non_api_key_app_configuration_should_fail(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
) -> None:
    body = LinkedAccountAPIKeyCreate(
        app_name=dummy_app_configuration_oauth2_google_project_1.app_name,
        linked_account_owner_id="test_link_api_key_account_under_non_api_key_app_configuration",
        api_key="test_linked_account_api_key",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=body.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert str(response.json()["error"]).startswith("No implementation found")
