from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import Plan
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.common.schemas.linked_accounts import (
    LinkedAccountAPIKeyCreate,
    LinkedAccountNoAuthCreate,
    LinkedAccountOAuth2Create,
)
from aci.server import config


def test_linked_accounts_quota_for_a_single_project_in_an_org(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_no_auth_mock_app_connector_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfigurationPublic,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    free_plan: Plan,
) -> None:
    # Given: User has already created the max number of unique linked account owner ids
    for i in range(free_plan.features["linked_accounts"]):
        linked_account_owner_id = f"test_linked_accounts_quota_{i}"
        body = LinkedAccountNoAuthCreate(
            app_name=dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
            linked_account_owner_id=linked_account_owner_id,
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
            json=body.model_dump(mode="json", exclude_none=True),
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_200_OK

    # Then: User can still create a new linked account with the same owner id in a
    # different app
    existing_linked_account_owner_id = (
        f"test_linked_accounts_quota_{free_plan.features['linked_accounts'] - 1}"
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=LinkedAccountAPIKeyCreate(
            app_name=dummy_app_configuration_api_key_aci_test_project_1.app_name,
            linked_account_owner_id=existing_linked_account_owner_id,
            api_key="aci_api_key",
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK

    # Then: User cannot create a new linked account with a new owner id in no-auth app
    new_linked_account_owner_id = (
        f"test_linked_accounts_quota_{free_plan.features['linked_accounts'] + 1}"
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=LinkedAccountNoAuthCreate(
            app_name=dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
            linked_account_owner_id=new_linked_account_owner_id,
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Then: User cannot create a new linked account with a new owner id in api-key app
    new_linked_account_owner_id = (
        f"test_linked_accounts_quota_{free_plan.features['linked_accounts'] + 2}"
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=LinkedAccountAPIKeyCreate(
            app_name=dummy_app_configuration_api_key_aci_test_project_1.app_name,
            linked_account_owner_id=new_linked_account_owner_id,
            api_key="aci_api_key",
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Then: User cannot create a new linked account with a new owner id in oauth2 app
    new_linked_account_owner_id = (
        f"test_linked_accounts_quota_{free_plan.features['linked_accounts'] + 3}"
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/oauth2",
        params=LinkedAccountOAuth2Create(
            app_name=dummy_app_configuration_oauth2_google_project_1.app_name,
            linked_account_owner_id=new_linked_account_owner_id,
            after_oauth2_link_redirect_url="https://example.com",
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_linked_accounts_quota_for_multiple_projects_in_an_org(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
    dummy_api_key_2: str,
    dummy_app_configuration_api_key_github_project_2: AppConfigurationPublic,
    free_plan: Plan,
) -> None:
    # Given: User has already created the max number of unique linked account owner ids
    # in project 1
    for i in range(free_plan.features["linked_accounts"]):
        linked_account_owner_id = f"test_linked_accounts_quota_{i}"
        body = LinkedAccountAPIKeyCreate(
            app_name=dummy_app_configuration_api_key_github_project_1.app_name,
            linked_account_owner_id=linked_account_owner_id,
            api_key="aci_api_key",
        )
        response = test_client.post(
            f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
            json=body.model_dump(mode="json", exclude_none=True),
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_200_OK

    # Then: User can still create a new linked account with an existing owner id in
    # project 2
    existing_linked_account_owner_id = (
        f"test_linked_accounts_quota_{free_plan.features['linked_accounts'] - 1}"
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=LinkedAccountAPIKeyCreate(
            app_name=dummy_app_configuration_api_key_github_project_2.app_name,
            linked_account_owner_id=existing_linked_account_owner_id,
            api_key="aci_api_key",
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == status.HTTP_200_OK

    # Then: User cannot create a new linked account with a new owner id in project 2
    new_linked_account_owner_id = (
        f"test_linked_accounts_quota_{free_plan.features['linked_accounts'] + 1}"
    )
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=LinkedAccountAPIKeyCreate(
            app_name=dummy_app_configuration_api_key_github_project_2.app_name,
            linked_account_owner_id=new_linked_account_owner_id,
            api_key="aci_api_key",
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_2},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_linked_accounts_quota_for_the_same_owner_id(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_no_auth_mock_app_connector_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfigurationPublic,
    free_plan: Plan,
) -> None:
    # Given: User has already linked the same owner id with two different apps
    same_owner_id = "test_same_owner_id"

    # Create linked account with no-auth app (mock app connector)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=LinkedAccountNoAuthCreate(
            app_name=dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
            linked_account_owner_id=same_owner_id,
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK

    # Create linked account with same owner ID but different app (github)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=LinkedAccountAPIKeyCreate(
            app_name=dummy_app_configuration_api_key_github_project_1.app_name,
            linked_account_owner_id=same_owner_id,
            api_key="aci_api_key",
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK

    # Then: User can create more unique owner IDs up to the quota limit (mock app connector)
    for i in range(1, free_plan.features["linked_accounts"]):
        unique_owner_id = f"unique_owner_{i}"
        response = test_client.post(
            f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
            json=LinkedAccountNoAuthCreate(
                app_name=dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
                linked_account_owner_id=unique_owner_id,
            ).model_dump(mode="json", exclude_none=True),
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_200_OK

    # Then: User can still create another linked account with the same owner ID in a different app (aci test)
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/api-key",
        json=LinkedAccountAPIKeyCreate(
            app_name=dummy_app_configuration_api_key_aci_test_project_1.app_name,
            linked_account_owner_id=same_owner_id,
            api_key="aci_api_key",
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK

    # Then: User cannot create a new linked account with a new unique owner ID (quota exceeded)
    new_unique_owner_id = f"unique_owner_{free_plan.features['linked_accounts']}"
    response = test_client.post(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/no-auth",
        json=LinkedAccountNoAuthCreate(
            app_name=dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
            linked_account_owner_id=new_unique_owner_id,
        ).model_dump(mode="json", exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
