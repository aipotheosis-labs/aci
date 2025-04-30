from typing import override, Dict, Any
from e2b_code_interpreter import Sandbox

from aci.common.db.sql_models import LinkedAccount
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)

class E2b(AppConnectorBase):
    """
    E2B.dev Sandbox Connector using Code Interpreter.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: APIKeyScheme,
        security_credentials: APIKeySchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        logger.info("Initializing E2B connector")
        logger.info(f"E2B API key: {self.security_credentials.secret_key}")
        # Initialize with None, will be set when creating a sandbox
        self.sandbox = None
        self.sandbox_id = None

    @override
    def _before_execute(self) -> None:
        # Nothing special needed before execution
        logger.info("Before execute hook called for E2B connector")
        pass

    def run_code(
        self,
        code: str,
    ) -> Dict[str, Any]:
        """
        List all running sandboxes
        """

        with Sandbox(
            api_key=self.security_credentials.secret_key
        ) as sandbox:
            execution = sandbox.run_code(code)
            logger.info(f"Execution: {execution}")
            return execution.text