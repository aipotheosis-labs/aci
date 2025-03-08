from typing import Any, override

from aipolabs.common.schemas.security_scheme import (
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aipolabs.server.app_connectors.base import AppConnectorBase


class MockAppConnector(AppConnectorBase[OAuth2Scheme, OAuth2SchemeCredentials]):
    """
    Mock app connector for testing.
    """

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
        }

    def fail(self) -> None:
        """Test function that always fails."""
        raise Exception("This function is designed to fail for testing purposes")
