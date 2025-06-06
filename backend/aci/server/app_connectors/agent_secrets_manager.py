from typing import override

from aci.common import encryption
from aci.common.db import crud
from aci.common.db.sql_models import LinkedAccount
from aci.common.exceptions import (
    AgentSecretsManagerError,
)
from aci.common.schemas.app_connectors.agent_secrets_manager import (
    DomainCredential,
    SecretValue,
)
from aci.common.schemas.secret import SecretCreate, SecretUpdate
from aci.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aci.common.utils import create_db_session
from aci.server import config, quota_manager
from aci.server.app_connectors.base import AppConnectorBase


class AgentSecretsManager(AppConnectorBase):
    """
    Agent Secrets Manager Connector that manages user credentials (username/password) for
    different domains.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: NoAuthScheme,
        security_credentials: NoAuthSchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)

    @override
    def _before_execute(self) -> None:
        pass

    def list_credentials(self) -> list[DomainCredential]:
        """
        Returns a list of all website credential secrets.

        Function name: AGENT_SECRETS_MANAGER__LIST_CREDENTIALS

        Returns:
            list[DomainCredential]: List of domain credentials.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            secrets = crud.secret.list_secrets(db_session, self.linked_account.id)

            result = []
            for secret in secrets:
                decrypted_value = encryption.decrypt(secret.value)
                secret_value = SecretValue.model_validate_json(decrypted_value.decode())

                result.append(DomainCredential(domain=secret.key, **secret_value.model_dump()))

            return result

    def get_credential_for_domain(self, domain: str) -> DomainCredential:
        """
        Retrieves the credential for a specific domain.

        Function name: AGENT_SECRETS_MANAGER__GET_CREDENTIAL_FOR_DOMAIN

        Args:
            domain (str): Domain to retrieve credentials for.

        Returns:
            DomainCredential: Dictionary containing username, password, and domain.

        Raises:
            KeyError: If no credential exists for the specified domain.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            secret = crud.secret.get_secret(db_session, self.linked_account.id, domain)
            if not secret:
                raise AgentSecretsManagerError(
                    message=f"No credentials found for domain '{domain}'"
                )

            decrypted_value = encryption.decrypt(secret.value)
            secret_value = SecretValue.model_validate_json(decrypted_value.decode())

            return DomainCredential(
                domain=domain,
                **secret_value.model_dump(),
            )

    def create_credential_for_domain(self, domain: str, username: str, password: str) -> None:
        """
        Creates a new credential for a specific domain.

        Function name: AGENT_SECRETS_MANAGER__CREATE_CREDENTIAL_FOR_DOMAIN

        Args:
            domain (str): Domain for the credential.
            username (str): Username for the credential.
            password (str): Password for the credential.

        Raises:
            AgentSecretsManagerError: If a credential for the domain already exists.
            MaxAgentSecretsReached: If the project has reached its maximum allowed agent secrets
            SubscriptionPlanNotFound: If the organization's subscription plan cannot be found
            ProjectNotFound: If the project cannot be found
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            existing = crud.secret.get_secret(db_session, self.linked_account.id, domain)
            if existing:
                raise AgentSecretsManagerError(
                    message=f"Credential for domain '{domain}' already exists"
                )

            # Check quota before creating new secret
            quota_manager.enforce_agent_secrets_quota(db_session, self.linked_account.project_id)

            secret_value = SecretValue(username=username, password=password)
            encrypted_value = encryption.encrypt(secret_value.model_dump_json().encode())

            secret_create = SecretCreate(
                key=domain,
                value=encrypted_value,
            )
            crud.secret.create_secret(db_session, self.linked_account.id, secret_create)
            db_session.commit()

    def update_credential_for_domain(self, domain: str, username: str, password: str) -> None:
        """
        Updates an existing credential for a specific domain.

        Function name: AGENT_SECRETS_MANAGER__UPDATE_CREDENTIAL_FOR_DOMAIN

        Args:
            domain (str): Domain for the credential to update.
            username (str): New username for the credential.
            password (str): New password for the credential.

        Raises:
            KeyError: If no credential exists for the specified domain.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            secret = crud.secret.get_secret(db_session, self.linked_account.id, domain)
            if not secret:
                raise AgentSecretsManagerError(
                    message=f"No credentials found for domain '{domain}'"
                )

            secret_value = SecretValue(username=username, password=password)
            encrypted_value = encryption.encrypt(secret_value.model_dump_json().encode())

            secret_update = SecretUpdate(
                value=encrypted_value,
            )
            crud.secret.update_secret(db_session, secret, secret_update)
            db_session.commit()

    def delete_credential_for_domain(self, domain: str) -> None:
        """
        Deletes a credential for a specific domain.

        Function name: AGENT_SECRETS_MANAGER__DELETE_CREDENTIAL_FOR_DOMAIN

        Args:
            domain (str): Domain for the credential to delete.

        Raises:
            KeyError: If no credential exists for the specified domain.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            secret = crud.secret.get_secret(db_session, self.linked_account.id, domain)
            if not secret:
                raise AgentSecretsManagerError(
                    message=f"No credentials found for domain '{domain}'"
                )
            crud.secret.delete_secret(db_session, secret)
            db_session.commit()
