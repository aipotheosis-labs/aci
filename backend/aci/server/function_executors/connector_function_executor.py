import importlib
from typing import Generic, override

from aci.common.db.sql_models import Function
from aci.common.exceptions import NoImplementationFound
from aci.common.logging_setup import get_logger
from aci.common.schemas.function import FunctionExecutionResult
from aci.common.schemas.security_scheme import (
    TCred,
    TScheme,
)
from aci.server.app_connectors.base import AppConnectorBase
from aci.server.function_executors.base_executor import FunctionExecutor

logger = get_logger(__name__)


def parse_function_name(function_name: str) -> tuple[str, str, str]:
    """
    Parse function name to get module name, class name and method name.
    e.g. "BRAVE_SEARCH__WEB_SEARCH" -> "aci.server.app_connectors.brave_search", "BraveSearch", "web_search"
    """
    app_name, method_name = function_name.split("__", 1)
    module_name = f"aci.server.app_connectors.{app_name.lower()}"
    class_name = "".join(word.capitalize() for word in app_name.split("_"))
    method_name = method_name.lower()

    return module_name, class_name, method_name


class ConnectorFunctionExecutor(FunctionExecutor[TScheme, TCred], Generic[TScheme, TCred]):
    """
    Function executor for local connector-based Apps/Functions.
    """

    @override
    def _execute(
        self,
        function: Function,
        function_input: dict,
        security_scheme: TScheme,
        security_credentials: TCred,
    ) -> FunctionExecutionResult:
        """
        Execute a function by importing the connector module and calling the function.
        """
        logger.info(
            "executing connector function",
            extra={"function_name": function.name},
        )
        module_name, class_name, method_name = parse_function_name(function.name)
        logger.info(
            "parsed function name",
            extra={
                "module_name": module_name,
                "class_name": class_name,
                "method_name": method_name,
            },
        )

        app_connector_class = self._get_app_connector_class(module_name, class_name)
        logger.info(
            "got app connector class",
            extra={"app_connector_class": app_connector_class},
        )
        # TODO: caching? singleton per app per enduser account? executing in a thread pool?
        # another tricky thing is the access token expiration if using long-live cached objects
        app_connector_instance = app_connector_class(
            self.linked_account, security_scheme, security_credentials
        )
        return app_connector_instance.execute(method_name, function_input)

    def _get_app_connector_class(self, module_name: str, class_name: str) -> type[AppConnectorBase]:
        """
        Get the app connector class.

        Returns:
            The app connector class.

        Raises:
            NoImplementationFound: If the app connector class is not found.
        """

        try:
            app_connector_class: type[AppConnectorBase] = getattr(
                importlib.import_module(module_name), class_name
            )
            logger.debug(
                "found app connector class",
                extra={
                    "module_name": module_name,
                    "class_name": class_name,
                    "app_connector_class": app_connector_class,
                },
            )
            return app_connector_class
        except (ImportError, AttributeError) as e:
            logger.exception(
                "failed to find app connector class",
                extra={"module_name": module_name, "class_name": class_name},
            )
            raise NoImplementationFound("no app connector class found") from e
