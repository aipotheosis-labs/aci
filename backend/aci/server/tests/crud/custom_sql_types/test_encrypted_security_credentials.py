import base64
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from aci.common import encryption
from aci.common.db.sql_models import App, LinkedAccount, Project
from aci.common.enums import SecurityScheme
from aci.common.schemas.security_scheme import APIKeySchemeCredentials, OAuth2SchemeCredentials


def test_linked_account_table_security_credentials_column_api_key_encryption(
    dummy_app_aci_test: App,
    dummy_project_1: Project,
    db_session: Session,
) -> None:
    """Test that LinkedAccount.security_credentials is correctly encrypted and decrypted
    for API key type security credentials.
    """
    # Given - Create test data
    expected_api_key = "very_secret_api_key"
    expected_default_security_credential = APIKeySchemeCredentials(
        secret_key=expected_api_key,
    ).model_dump()

    # Given - Create and save LinkedAccount with security_credentials
    linked_account = LinkedAccount(
        project_id=dummy_project_1.id,
        app_id=dummy_app_aci_test.id,
        linked_account_owner_id="test_owner",
        security_scheme=SecurityScheme.API_KEY,
        security_credentials=expected_default_security_credential,
        enabled=True,
    )
    db_session.add(linked_account)
    db_session.commit()

    # When - Clear session and retrieve the LinkedAccount
    linked_account_id = linked_account.id
    db_session.expunge_all()
    retrieved_linked_account = (
        db_session.query(LinkedAccount).filter_by(id=linked_account_id).first()
    )
    assert retrieved_linked_account is not None

    # Then - the linked account retrieved from the database should have the same api key
    retrieved_api_key_scheme_credentials = APIKeySchemeCredentials.model_validate(
        retrieved_linked_account.security_credentials
    )
    assert retrieved_api_key_scheme_credentials.secret_key == expected_api_key

    # Then - Verify the value is actually encrypted in the database
    raw_query = text("SELECT security_credentials FROM linked_accounts WHERE id = :id")
    result = db_session.execute(raw_query, {"id": str(linked_account_id)}).first()
    raw_security_credentials = result[0] if result else None
    assert raw_security_credentials is not None
    assert isinstance(raw_security_credentials, dict)

    raw_secret_key = raw_security_credentials["secret_key"]
    assert raw_secret_key is not None
    assert raw_secret_key != expected_api_key

    # Then - Decrypt the value and verify it matches the original value
    decrypted_secret_key = encryption.decrypt(base64.b64decode(raw_secret_key)).decode("utf-8")
    assert decrypted_secret_key == expected_api_key


def test_linked_account_table_security_credentials_column_oauth2_encryption(
    dummy_app_aci_test: App,
    dummy_project_1: Project,
    db_session: Session,
) -> None:
    """Test that LinkedAccount.security_credentials is correctly encrypted and decrypted
    for OAuth2 type security credentials.
    """
    # Given - Create test data
    expected_client_id = "test_client_id"
    expected_client_secret = "test_client_secret"
    expected_access_token = "test_access_token"
    expected_refresh_token = "test_refresh_token"
    expected_raw_token_response = {"key": "value"}
    expected_default_security_credential = OAuth2SchemeCredentials(
        client_id=expected_client_id,
        client_secret=expected_client_secret,
        scope="test",
        access_token=expected_access_token,
        token_type="Bearer",
        expires_at=1234567890,
        refresh_token=expected_refresh_token,
        raw_token_response=expected_raw_token_response,
    ).model_dump()

    # Given - Create and save LinkedAccount with security_credentials
    linked_account = LinkedAccount(
        project_id=dummy_project_1.id,
        app_id=dummy_app_aci_test.id,
        linked_account_owner_id="test_owner",
        security_scheme=SecurityScheme.OAUTH2,
        security_credentials=expected_default_security_credential,
        enabled=True,
    )
    db_session.add(linked_account)
    db_session.commit()

    # When - Clear session and retrieve the LinkedAccount
    linked_account_id = linked_account.id
    db_session.expunge_all()
    retrieved_linked_account = (
        db_session.query(LinkedAccount).filter_by(id=linked_account_id).first()
    )
    assert retrieved_linked_account is not None

    # Then - the linked account retrieved from the database should have the same oauth2 credentials
    retrieved_oauth2_scheme_credentials = OAuth2SchemeCredentials.model_validate(
        retrieved_linked_account.security_credentials
    )
    assert retrieved_oauth2_scheme_credentials.client_id == expected_client_id
    assert retrieved_oauth2_scheme_credentials.client_secret == expected_client_secret
    assert retrieved_oauth2_scheme_credentials.access_token == expected_access_token
    assert retrieved_oauth2_scheme_credentials.refresh_token == expected_refresh_token
    assert retrieved_oauth2_scheme_credentials.raw_token_response == expected_raw_token_response

    # When - Retrieve the raw security credentials from the database
    raw_query = text("SELECT security_credentials FROM linked_accounts WHERE id = :id")
    result = db_session.execute(raw_query, {"id": str(linked_account_id)}).first()
    raw_security_credentials = result[0] if result else None
    assert raw_security_credentials is not None
    assert isinstance(raw_security_credentials, dict)

    # Then - Verify client_secret is encrypted and can be decrypted to the original value
    raw_client_secret = raw_security_credentials["client_secret"]
    assert raw_client_secret is not None
    assert raw_client_secret != expected_client_secret

    decrypted_client_secret = encryption.decrypt(base64.b64decode(raw_client_secret)).decode(
        "utf-8"
    )
    assert decrypted_client_secret == expected_client_secret

    # Then - Verify access_token is encrypted and can be decrypted to the original value
    raw_access_token = raw_security_credentials["access_token"]
    assert raw_access_token is not None
    assert raw_access_token != expected_access_token

    decrypted_access_token = encryption.decrypt(base64.b64decode(raw_access_token)).decode("utf-8")
    assert decrypted_access_token == expected_access_token

    # Then - Verify refresh_token is encrypted and can be decrypted to the original value
    raw_refresh_token = raw_security_credentials["refresh_token"]
    assert raw_refresh_token is not None
    assert raw_refresh_token != expected_refresh_token

    decrypted_refresh_token = encryption.decrypt(base64.b64decode(raw_refresh_token)).decode(
        "utf-8"
    )
    assert decrypted_refresh_token == expected_refresh_token

    # Then - Verify raw_token_response is encrypted and can be decrypted to the original value
    raw_raw_token_response = raw_security_credentials["raw_token_response"]
    assert raw_raw_token_response is not None
    assert raw_raw_token_response != expected_raw_token_response

    decrypted_raw_token_response = encryption.decrypt(
        base64.b64decode(raw_raw_token_response)
    ).decode("utf-8")
    assert json.loads(decrypted_raw_token_response) == expected_raw_token_response


def test_linked_account_table_security_credentials_column_mutable_dict_detection(
    db_session: Session,
    dummy_app_aci_test: App,
    dummy_project_1: Project,
) -> None:
    """Test that LinkedAccount.security_credentials is correctly detected as a mutable dict, meaning
    when the first level fields of the json changed, SQLAlchemy will detect it as a change
    and save it to the database.
    """
    # Given - Create test data
    expected_token_type = "Bearer"
    expected_default_security_credential = OAuth2SchemeCredentials(
        client_id="test",
        client_secret="test",
        scope="test",
        access_token="test_access_token",
        token_type=expected_token_type,
        expires_at=1234567890,
        refresh_token="test_refresh_token",
        raw_token_response={"key": "value"},
    ).model_dump()

    # Given - Create and save LinkedAccount with security_credentials
    linked_account = LinkedAccount(
        project_id=dummy_project_1.id,
        app_id=dummy_app_aci_test.id,
        linked_account_owner_id="test_owner",
        security_scheme=SecurityScheme.OAUTH2,
        security_credentials=expected_default_security_credential,
        enabled=True,
    )
    db_session.add(linked_account)
    db_session.commit()

    # When - Update the security_credentials
    new_token_type = "ACI"
    linked_account.security_credentials["token_type"] = new_token_type
    db_session.commit()

    # Then - The change is detected and saved to the database
    linked_account_id = linked_account.id
    db_session.expunge_all()
    retrieved_linked_account = (
        db_session.query(LinkedAccount).filter_by(id=linked_account_id).first()
    )
    assert retrieved_linked_account is not None
    assert retrieved_linked_account.security_credentials["token_type"] == new_token_type
