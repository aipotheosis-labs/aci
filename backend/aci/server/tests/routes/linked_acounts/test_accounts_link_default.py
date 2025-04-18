import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import App
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.common.schemas.linked_accounts import LinkedAccountDefaultCreate
from aci.server import config

MOCK_GOOGLE_AUTH_REDIRECT_URI_PREFIX = (
    "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&"
)
ENDPOINT = f"{config.ROUTER_PREFIX_LINKED_ACCOUNTS}/default"


def test_link_account_with_default_api_key_credentials(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfigurationPublic,
    db_session: Session,
) -> None:
    # link account with default apikey credentials
    body = LinkedAccountDefaultCreate(
        app_name=dummy_app_configuration_api_key_aci_test_project_1.app_name,
        linked_account_owner_id="test_link_account_with_default_api_key_credentials_success",
    )
    response = test_client.post(
        ENDPOINT,
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK, response.json()

    # confirm linked account is created with correct values
    linked_account = crud.linked_accounts.get_linked_account(
        db_session,
        dummy_app_configuration_api_key_aci_test_project_1.project_id,
        dummy_app_configuration_api_key_aci_test_project_1.app_name,
        body.linked_account_owner_id,
    )
    assert linked_account is not None
    assert (
        linked_account.project_id == dummy_app_configuration_api_key_aci_test_project_1.project_id
    )
    assert linked_account.app.name == dummy_app_configuration_api_key_aci_test_project_1.app_name
    assert linked_account.linked_account_owner_id == body.linked_account_owner_id
    assert (
        linked_account.security_scheme
        == dummy_app_configuration_api_key_aci_test_project_1.security_scheme
    )
    assert linked_account.security_credentials == {}, (
        "linked account using default credentials should have empty security credentials"
    )
    assert linked_account.enabled is True


@pytest.mark.skip(reason="TODO: implement")
def test_link_account_with_default_oauth2_credentials(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
    db_session: Session,
) -> None:
    """
    TODO: implement
    Make sure dummy_app_configuration_oauth2_google_project_1 has default dummy oauth2 credentials
    """
    pass


def test_link_account_with_default_credentials_non_existent_app_configuration(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_github: App,
) -> None:
    body = LinkedAccountDefaultCreate(
        app_name=dummy_app_github.name,
        linked_account_owner_id="test_link_account_with_default_credentials_non_existent_app_configuration",
    )
    response = test_client.post(
        ENDPOINT,
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert str(response.json()["error"]).startswith("App configuration not found")


def test_link_account_with_default_credentials_app_without_default_credentials(
    test_client: TestClient,
    dummy_api_key_1: str,
    dummy_app_github: App,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
    db_session: Session,
) -> None:
    # remove the default credentials from the dummy app
    dummy_app_github.default_security_credentials_by_scheme = {}
    db_session.commit()

    # try to link account using default credentials
    body = LinkedAccountDefaultCreate(
        app_name=dummy_app_github.name,
        linked_account_owner_id="test_link_account_with_default_credentials_app_without_default_credentials",
    )
    response = test_client.post(
        ENDPOINT,
        json=body.model_dump(mode="json"),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert str(response.json()["error"]).startswith("No implementation found")
