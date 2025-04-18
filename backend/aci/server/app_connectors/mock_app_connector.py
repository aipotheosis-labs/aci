from typing import Any, override

from aci.common.db.sql_models import LinkedAccount
from aci.common.schemas.security_scheme import (
    NoAuthScheme,
    NoAuthSchemeCredentials,
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase


class MockAppConnector(AppConnectorBase):
    """
    Mock app connector for testing.
    An App can support multiple security schemes, so the app connector should be able to handle that as well.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: OAuth2Scheme | NoAuthScheme,
        security_credentials: OAuth2SchemeCredentials | NoAuthSchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        if isinstance(self.security_scheme, NoAuthScheme):
            pass
        else:
            pass

    @override
    def _before_execute(self) -> None:
        pass

    def echo(
        self,
        input_string: str,
        input_int: int,
        input_bool: bool,
        input_list: list[str],
        input_required_invisible_string: str,
    ) -> dict[str, Any]:
        """Test function that returns the input parameter."""
        return {
            "input_string": input_string,
            "input_int": input_int,
            "input_bool": input_bool,
            "input_list": input_list,
            "input_required_invisible_string": input_required_invisible_string,
            "security_scheme": self.linked_account.security_scheme,
            "security_scheme_cls": type(self.security_scheme).__name__,
            "security_credentials_cls": type(self.security_credentials).__name__,
        }

    def fail(self) -> None:
        """Test function that always fails."""
        raise Exception("This function is designed to fail for testing purposes")
