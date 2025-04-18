from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import App, LinkedAccount
from aci.server import config


def test_list_linked_accounts_no_filters(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 2, "Should only return linked accounts under dummy project 1"


def test_list_linked_accounts_filter_by_app_name(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}",
        headers={"x-api-key": dummy_api_key_1},
        params={"app_name": dummy_linked_account_oauth2_google_project_1.app.name},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1, (
        "Should only return linked accounts of google app under dummy project 1"
    )
    assert response.json()[0]["app_name"] == dummy_linked_account_oauth2_google_project_1.app.name
    assert (
        response.json()[0]["linked_account_owner_id"]
        == dummy_linked_account_oauth2_google_project_1.linked_account_owner_id
    )


def test_list_linked_accounts_filter_by_account_name(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}",
        headers={"x-api-key": dummy_api_key_1},
        params={
            "linked_account_owner_id": (
                dummy_linked_account_api_key_github_project_1.linked_account_owner_id
            )
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1, (
        "Should only return linked accounts of specific account owner under dummy project 1"
    )
    assert response.json()[0]["app_name"] == dummy_linked_account_api_key_github_project_1.app.name
    assert (
        response.json()[0]["linked_account_owner_id"]
        == dummy_linked_account_api_key_github_project_1.linked_account_owner_id
    )


def test_list_linked_accounts_filter_by_app_name_and_account_owner_id(
    test_client: TestClient,
    dummy_api_key_2: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
    dummy_linked_account_api_key_github_project_1: LinkedAccount,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}",
        headers={"x-api-key": dummy_api_key_2},
        params={
            "app_name": dummy_linked_account_oauth2_google_project_2.app.name,
            "linked_account_owner_id": (
                dummy_linked_account_oauth2_google_project_2.linked_account_owner_id,
            ),
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 1
    assert response.json()[0]["app_name"] == dummy_linked_account_oauth2_google_project_2.app.name
    assert (
        response.json()[0]["linked_account_owner_id"]
        == dummy_linked_account_oauth2_google_project_2.linked_account_owner_id
    )


def test_list_linked_accounts_filter_by_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_aci_test: App,
) -> None:
    response = test_client.get(
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}",
        headers={"x-api-key": dummy_api_key_1},
        params={"app_name": dummy_app_aci_test.name},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()) == 0
