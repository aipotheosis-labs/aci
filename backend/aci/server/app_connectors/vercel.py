from typing import Any, override

from aci.common.db.sql_models import LinkedAccount
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


class Vercel(AppConnectorBase):
    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: APIKeyScheme,
        security_credentials: APIKeySchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        self.api_key = security_credentials.secret_key

    @override
    def _before_execute(self) -> None:
        pass

    def get_url_to_install_vercel_app_in_github(self) -> dict[str, Any]:
        """
        Get the URL to install the Vercel app in a GitHub repository.
        """
        return {
            "url": "https://github.com/apps/vercel/installations/select_target",
            "description": "Asks the user to use this URL to install the Vercel app in their GitHub account.",
        }
