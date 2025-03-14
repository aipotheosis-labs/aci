import json
from typing import override

from aipolabs.common import encryption
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import LinkedAccount
from aipolabs.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aipolabs.common.utils import create_db_session
from aipolabs.server import config
from aipolabs.server.app_connectors.base import AppConnectorBase


class DomainCredential(dict[str, str]):
    username: str
    password: str
    domain: str


class AipolabsSecretsManager(AppConnectorBase):
    """
    Aipolabs Secrets Manager Connector that manages user credentials (username/password) for
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

        Function name: AIPOLABS_SECRETS_MANAGER__LIST_CREDENTIALS

        Returns:
            list[DomainCredential]: List of domain credentials.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            secrets = crud.secret.list_secrets(db_session, self.linked_account.id)

            result = []
            for secret in secrets:
                decrypted_value = encryption.decrypt(secret.value)
                secret_value = json.loads(decrypted_value.decode())

                result.append(
                    DomainCredential(
                        domain=secret.key,
                        username=secret_value["username"],
                        password=secret_value["password"],
                    )
                )

            return result

    def get_credential_for_domain(self, domain: str) -> DomainCredential:
        """
        Retrieves the credential for a specific domain.

        Function name: AIPOLABS_SECRETS_MANAGER__GET_CREDENTIAL_FOR_DOMAIN

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
                raise KeyError(f"No credentials found for domain '{domain}'")

            decrypted_value = encryption.decrypt(secret.value)
            secret_value = json.loads(decrypted_value.decode())

            return DomainCredential(
                domain=domain,
                username=secret_value["username"],
                password=secret_value["password"],
            )

    def create_credential_for_domain(self, domain: str, username: str, password: str) -> None:
        """
        Creates a new credential for a specific domain.

        Function name: AIPOLABS_SECRETS_MANAGER__CREATE_CREDENTIAL_FOR_DOMAIN

        Args:
            domain (str): Domain for the credential.
            username (str): Username for the credential.
            password (str): Password for the credential.

        Raises:
            ValueError: If a credential for the domain already exists.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            existing = crud.secret.get_secret(db_session, self.linked_account.id, domain)
            if existing:
                raise ValueError(f"Credential for domain '{domain}' already exists")

            secret_value = {
                "username": username,
                "password": password,
            }

            json_bytes = json.dumps(secret_value).encode()
            encrypted_value = encryption.encrypt(json_bytes)

            crud.secret.create_secret(db_session, self.linked_account.id, domain, encrypted_value)
            db_session.commit()

    def update_credential_for_domain(self, domain: str, username: str, password: str) -> None:
        """
        Updates an existing credential for a specific domain.

        Function name: AIPOLABS_SECRETS_MANAGER__UPDATE_CREDENTIAL_FOR_DOMAIN

        Args:
            domain (str): Domain for the credential to update.
            username (str): New username for the credential.
            password (str): New password for the credential.

        Raises:
            KeyError: If no credential exists for the specified domain.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            secret_value = {
                "username": username,
                "password": password,
            }

            json_bytes = json.dumps(secret_value).encode()
            encrypted_value = encryption.encrypt(json_bytes)

            crud.secret.update_secret(db_session, self.linked_account.id, domain, encrypted_value)
            db_session.commit()

    def delete_credential_for_domain(self, domain: str) -> None:
        """
        Deletes a credential for a specific domain.

        Function name: AIPOLABS_SECRETS_MANAGER__DELETE_CREDENTIAL_FOR_DOMAIN

        Args:
            domain (str): Domain for the credential to delete.

        Raises:
            KeyError: If no credential exists for the specified domain.
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            crud.secret.delete_secret(db_session, self.linked_account.id, domain)
            db_session.commit()
