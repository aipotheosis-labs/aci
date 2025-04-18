from fastapi import status
from fastapi.testclient import TestClient

from aci.common.db.sql_models import LinkedAccount
from aci.common.schemas.linked_accounts import LinkedAccountPublic, LinkedAccountUpdate
from aci.server import config

NON_EXISTENT_LINKED_ACCOUNT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_update_linked_account(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_1.id}"
    )

    assert dummy_linked_account_oauth2_google_project_1.enabled, (
        "linked account should be enabled by default"
    )

    linked_account_update = LinkedAccountUpdate(enabled=False)
    response = test_client.patch(
        ENDPOINT, headers={"x-api-key": dummy_api_key_1}, json=linked_account_update.model_dump()
    )
    assert response.status_code == status.HTTP_200_OK
    linked_account_response = LinkedAccountPublic.model_validate(response.json())
    assert linked_account_response.enabled == linked_account_update.enabled


def test_update_linked_account_not_found(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
) -> None:
    ENDPOINT = f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{NON_EXISTENT_LINKED_ACCOUNT_ID}"

    linked_account_update = LinkedAccountUpdate(enabled=False)
    response = test_client.patch(
        ENDPOINT, headers={"x-api-key": dummy_api_key_1}, json=linked_account_update.model_dump()
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_linked_account_not_belong_to_project(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_linked_account_oauth2_google_project_1: LinkedAccount,
    dummy_linked_account_oauth2_google_project_2: LinkedAccount,
) -> None:
    ENDPOINT = (
        f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/{dummy_linked_account_oauth2_google_project_2.id}"
    )

    linked_account_update = LinkedAccountUpdate(enabled=False)

    response = test_client.patch(
        ENDPOINT, headers={"x-api-key": dummy_api_key_1}, json=linked_account_update.model_dump()
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, (
        "updating linked account that does not belong to the project should return 404"
    )
