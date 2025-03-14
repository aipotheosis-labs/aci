import json
from unittest.mock import MagicMock, patch

import pytest

from aipolabs.common.db.sql_models import LinkedAccount
from aipolabs.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aipolabs.server.app_connectors.aipolabs_secrets_manager import (
    AipolabsSecretsManager,
    DomainCredential,
)


@pytest.fixture
def secrets_manager() -> AipolabsSecretsManager:
    linked_account = MagicMock(spec=LinkedAccount)
    linked_account.id = "test_linked_account_id"

    security_scheme = MagicMock(spec=NoAuthScheme)
    security_credentials = MagicMock(spec=NoAuthSchemeCredentials)

    return AipolabsSecretsManager(
        linked_account=linked_account,
        security_scheme=security_scheme,
        security_credentials=security_credentials,
    )


def test_list_credentials(secrets_manager: AipolabsSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()

    mock_secret1 = MagicMock()
    mock_secret1.name = "example.com"
    mock_secret1.value = b"encrypted_value_1"

    mock_secret2 = MagicMock()
    mock_secret2.name = "test.com"
    mock_secret2.value = b"encrypted_value_2"

    with (
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.list_secrets",
            return_value=[mock_secret1, mock_secret2],
        ) as mock_list_secrets,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.encryption.decrypt",
            side_effect=[
                b'{"username": "user1", "password": "pass1"}',
                b'{"username": "user2", "password": "pass2"}',
            ],
        ),
    ):
        # When
        result = secrets_manager.list_credentials()

        # Then
        mock_create_db_session.assert_called_once()
        mock_list_secrets.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id
        )

        assert len(result) == 2
        assert isinstance(result[0], DomainCredential)
        assert isinstance(result[1], DomainCredential)

        assert result[0]["domain"] == "example.com"
        assert result[0]["username"] == "user1"
        assert result[0]["password"] == "pass1"

        assert result[1]["domain"] == "test.com"
        assert result[1]["username"] == "user2"
        assert result[1]["password"] == "pass2"


def test_get_credential_for_domain_success(secrets_manager: AipolabsSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()
    mock_secret = MagicMock()
    mock_secret.name = "example.com"
    mock_secret.value = b"encrypted_value"

    with (
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.get_secret",
            return_value=mock_secret,
        ) as mock_get_secret,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.encryption.decrypt",
            return_value=b'{"username": "user1", "password": "pass1"}',
        ) as mock_decrypt,
    ):
        # When
        result = secrets_manager.get_credential_for_domain("example.com")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )
        mock_decrypt.assert_called_once_with(b"encrypted_value")

        assert isinstance(result, DomainCredential)
        assert result["domain"] == "example.com"
        assert result["username"] == "user1"
        assert result["password"] == "pass1"


def test_get_credential_for_domain_not_found(secrets_manager: AipolabsSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()

    with (
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.get_secret",
            return_value=None,
        ) as mock_get_secret,
    ):
        # When
        with pytest.raises(KeyError, match="No credentials found for domain 'nonexistent.com'"):
            secrets_manager.get_credential_for_domain("nonexistent.com")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "nonexistent.com"
        )


def test_create_credential_for_domain_success(secrets_manager: AipolabsSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()
    encrypted_value = b"encrypted_value"

    with (
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.get_secret",
            return_value=None,
        ) as mock_get_secret,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.create_secret",
        ) as mock_create_secret,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.encryption.encrypt",
            return_value=encrypted_value,
        ) as mock_encrypt,
    ):
        # When
        secrets_manager.create_credential_for_domain("example.com", "user1", "pass1")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )

        expected_json = json.dumps({"username": "user1", "password": "pass1"}).encode()
        mock_encrypt.assert_called_once_with(expected_json)

        mock_create_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com", encrypted_value
        )
        mock_db_session.commit.assert_called_once()


def test_create_credential_for_domain_already_exists(
    secrets_manager: AipolabsSecretsManager,
) -> None:
    # Given
    mock_db_session = MagicMock()
    mock_secret = MagicMock()

    with (
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.get_secret",
            return_value=mock_secret,
        ) as mock_get_secret,
    ):
        # When
        with pytest.raises(ValueError, match="Credential for domain 'example.com' already exists"):
            secrets_manager.create_credential_for_domain("example.com", "user1", "pass1")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )


def test_update_credential_for_domain(secrets_manager: AipolabsSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()
    encrypted_value = b"encrypted_value"

    with (
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.update_secret",
        ) as mock_update_secret,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.encryption.encrypt",
            return_value=encrypted_value,
        ) as mock_encrypt,
    ):
        # When
        secrets_manager.update_credential_for_domain("example.com", "user_updated", "pass_updated")

        # Then
        mock_create_db_session.assert_called_once()

        expected_json = json.dumps(
            {"username": "user_updated", "password": "pass_updated"}
        ).encode()
        mock_encrypt.assert_called_once_with(expected_json)

        mock_update_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com", encrypted_value
        )
        mock_db_session.commit.assert_called_once()


def test_delete_credential_for_domain(secrets_manager: AipolabsSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()

    with (
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aipolabs.server.app_connectors.aipolabs_secrets_manager.crud.secret.delete_secret",
        ) as mock_delete_secret,
    ):
        # When
        secrets_manager.delete_credential_for_domain("example.com")

        # Then
        mock_create_db_session.assert_called_once()
        mock_delete_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )
        mock_db_session.commit.assert_called_once()
