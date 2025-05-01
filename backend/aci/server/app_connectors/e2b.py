from typing import Any, override

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
        self.api_key = security_credentials.secret_key

    @override
    def _before_execute(self) -> None:
        pass

    def run_code(
        self,
        code: str,
    ) -> dict[str, Any]:
        """
        Execute code in E2B sandbox and return the result.
        """
        with Sandbox(api_key=self.api_key) as sandbox:
            execution = sandbox.run_code(code)
            return {"text": execution.text}
