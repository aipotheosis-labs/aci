from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import LinkedAccount
from aci.server import config

NON_EXISTENT_LINKED_ACCOUNT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_delete_linked_account(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_1.id}"
    )

    response = test_client.delete(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # check that the linked account was deleted
    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{NON_EXISTENT_LINKED_ACCOUNT_ID}"

    response = test_client.delete(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_linked_account_not_belong_to_project(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_2.id}"
    )

    response = test_client.delete(ENDPOINT, headers={"x-api-key": dummy_api_key_1})

    assert response.status_code == status.HTTP_404_NOT_FOUND, (
        "Deleting linked account that does not belong to the project should return 404"
    )
