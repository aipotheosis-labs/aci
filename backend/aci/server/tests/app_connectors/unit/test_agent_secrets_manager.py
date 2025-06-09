import json
from unittest.mock import MagicMock, patch

import pytest

from aci.common.db.sql_models import LinkedAccount
from aci.common.exceptions import AgentSecretsManagerError
from aci.common.schemas.secret import SecretCreate, SecretUpdate
from aci.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aci.server.app_connectors.agent_secrets_manager import (
    AgentSecretsManager,
    DomainCredential,
)


@pytest.fixture
def secrets_manager() -> AgentSecretsManager:
    linked_account = MagicMock(spec=LinkedAccount)
    linked_account.id = "test_linked_account_id"

    security_scheme = MagicMock(spec=NoAuthScheme)
    security_credentials = MagicMock(spec=NoAuthSchemeCredentials)

    return AgentSecretsManager(
        linked_account=linked_account,
        security_scheme=security_scheme,
        security_credentials=security_credentials,
    )


def test_list_credentials(secrets_manager: AgentSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()

    mock_secret1 = MagicMock()
    mock_secret1.key = "example.com"
    mock_secret1.value = b"encrypted_value_1"

    mock_secret2 = MagicMock()
    mock_secret2.key = "test.com"
    mock_secret2.value = b"encrypted_value_2"

    with (
        patch(
            "aci.server.app_connectors.agent_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.list_secrets",
            return_value=[mock_secret1, mock_secret2],
        ) as mock_list_secrets,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.encryption.decrypt",
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

        domain_credential1 = DomainCredential.model_validate(result[0])
        domain_credential2 = DomainCredential.model_validate(result[1])

        assert domain_credential1.domain == "example.com"
        assert domain_credential1.username == "user1"
        assert domain_credential1.password == "pass1"

        assert domain_credential2.domain == "test.com"
        assert domain_credential2.username == "user2"
        assert domain_credential2.password == "pass2"


def test_get_credential_for_domain_success(secrets_manager: AgentSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()
    mock_secret = MagicMock()
    mock_secret.key = "example.com"
    mock_secret.value = b"encrypted_value"

    with (
        patch(
            "aci.server.app_connectors.agent_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.get_secret",
            return_value=mock_secret,
        ) as mock_get_secret,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.encryption.decrypt",
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

        domain_credential = DomainCredential.model_validate(result)
        assert domain_credential.domain == "example.com"
        assert domain_credential.username == "user1"
        assert domain_credential.password == "pass1"


def test_get_credential_for_domain_not_found(secrets_manager: AgentSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()

    with (
        patch(
            "aci.server.app_connectors.agent_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.get_secret",
            return_value=None,
        ) as mock_get_secret,
    ):
        # When
        with pytest.raises(
            AgentSecretsManagerError, match="No credentials found for domain 'nonexistent.com'"
        ):
            secrets_manager.get_credential_for_domain("nonexistent.com")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "nonexistent.com"
        )


def test_create_credential_for_domain_success(secrets_manager: AgentSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()
    encrypted_value = b"encrypted_value"
    mock_secret_create = MagicMock(spec=SecretCreate)

    with (
        patch(
            "aci.server.app_connectors.agent_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.get_secret",
            return_value=None,
        ) as mock_get_secret,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.create_secret",
        ) as mock_create_secret,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.encryption.encrypt",
            return_value=encrypted_value,
        ) as mock_encrypt,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.SecretCreate",
            return_value=mock_secret_create,
        ) as mock_secret_create_class,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.quota_manager.enforce_agent_secrets_quota",
        ),
    ):
        # When
        secrets_manager.create_credential_for_domain("example.com", "user1", "pass1")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )

        expected_json = json.dumps(
            {"username": "user1", "password": "pass1"}, separators=(",", ":")
        ).encode()
        mock_encrypt.assert_called_once_with(expected_json)

        mock_secret_create_class.assert_called_once_with(key="example.com", value=encrypted_value)
        mock_create_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, mock_secret_create
        )
        mock_db_session.commit.assert_called_once()


def test_create_credential_for_domain_already_exists(
    secrets_manager: AgentSecretsManager,
) -> None:
    # Given
    mock_db_session = MagicMock()
    mock_secret = MagicMock()

    with (
        patch(
            "aci.server.app_connectors.agent_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.get_secret",
            return_value=mock_secret,
        ) as mock_get_secret,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.quota_manager.enforce_agent_secrets_quota",
        ),
    ):
        # When
        with pytest.raises(
            AgentSecretsManagerError, match="Credential for domain 'example.com' already exists"
        ):
            secrets_manager.create_credential_for_domain("example.com", "user1", "pass1")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )


def test_update_credential_for_domain(secrets_manager: AgentSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()
    encrypted_value = b"encrypted_value"
    mock_secret = MagicMock()
    mock_secret_update = MagicMock(spec=SecretUpdate)

    with (
        patch(
            "aci.server.app_connectors.agent_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.get_secret",
            return_value=mock_secret,
        ) as mock_get_secret,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.update_secret",
        ) as mock_update_secret,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.encryption.encrypt",
            return_value=encrypted_value,
        ) as mock_encrypt,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.SecretUpdate",
            return_value=mock_secret_update,
        ) as mock_secret_update_class,
    ):
        # When
        secrets_manager.update_credential_for_domain("example.com", "user_updated", "pass_updated")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )

        expected_json = json.dumps(
            {"username": "user_updated", "password": "pass_updated"}, separators=(",", ":")
        ).encode()
        mock_encrypt.assert_called_once_with(expected_json)

        mock_secret_update_class.assert_called_once_with(value=encrypted_value)
        mock_update_secret.assert_called_once_with(mock_db_session, mock_secret, mock_secret_update)
        mock_db_session.commit.assert_called_once()


def test_delete_credential_for_domain(secrets_manager: AgentSecretsManager) -> None:
    # Given
    mock_db_session = MagicMock()
    mock_secret = MagicMock()

    with (
        patch(
            "aci.server.app_connectors.agent_secrets_manager.create_db_session",
            return_value=MagicMock(__enter__=MagicMock(return_value=mock_db_session)),
        ) as mock_create_db_session,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.get_secret",
            return_value=mock_secret,
        ) as mock_get_secret,
        patch(
            "aci.server.app_connectors.agent_secrets_manager.crud.secret.delete_secret",
        ) as mock_delete_secret,
    ):
        # When
        secrets_manager.delete_credential_for_domain("example.com")

        # Then
        mock_create_db_session.assert_called_once()
        mock_get_secret.assert_called_once_with(
            mock_db_session, secrets_manager.linked_account.id, "example.com"
        )
        mock_delete_secret.assert_called_once_with(mock_db_session, mock_secret)
        mock_db_session.commit.assert_called_once()
