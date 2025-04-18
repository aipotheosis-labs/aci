from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import LinkedAccount
from aci.common.schemas.linked_accounts import LinkedAccountPublic
from aci.server import config

NON_EXISTENT_LINKED_ACCOUNT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_get_linked_account(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_api_key_2: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
) -> None:
    ENDPOINT_1 = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_1.id}"
    )
    ENDPOINT_2 = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_2.id}"
    )

    response = test_client.get(ENDPOINT_1, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert (
        LinkedAccountPublic.model_validate(response.json()).id
        == dummy_linked_account_oauth2_google_project_1.id
    )

    response = test_client.get(ENDPOINT_2, headers={"x-api-key": dummy_api_key_2})
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert (
        LinkedAccountPublic.model_validate(response.json()).id
        == dummy_linked_account_oauth2_google_project_2.id
    )


def test_get_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{NON_EXISTENT_LINKED_ACCOUNT_ID}"

    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_linked_account_not_belong_to_project(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_2.id}"
    )

    response = test_client.get(ENDPOINT, headers={"x-api-key": dummy_api_key_1})
    assert response.status_code == status.HTTP_404_NOT_FOUND
