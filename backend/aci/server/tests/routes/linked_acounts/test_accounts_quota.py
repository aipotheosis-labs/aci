from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import Plan
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.common.schemas.linked_accounts import LinkedAccountNoAuthCreate
from aci.server import config


def test_linked_accounts_quota(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_no_auth_mock_app_connector_project_1: AppConfigurationPublic,
    free_plan: Plan,
) -> None:
    # Create first linked account (should succeed)
    body1 = LinkedAccountNoAuthCreate(
        app_name=dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
        linked_account_owner_id="test_linked_accounts_quota_1",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=body1.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to create third linked account (should fail due to quota)
    body2 = LinkedAccountNoAuthCreate(
        app_name=dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
        linked_account_owner_id="test_linked_accounts_quota_3",
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=body2.model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Max linked accounts reached" in str(response.json()["error"])
