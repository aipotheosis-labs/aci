import importlib
from abc import ABC
from typing import Type

from jsonschema import ValidationError, validate

from aipolabs.common.exceptions import InvalidFunctionInput, NoImplementationFound
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.function import FunctionExecutionResult

logger = get_logger(__name__)


def parse_function_name(function_name: str) -> tuple[str, str, str]:
    """
    Parse function name to get module name, class name and method name.
    e.g. "AIPOLABS_TEST__HELLO_WORLD" -> "aipolabs.server.apps.aipolabs_test", "AipolabsTest", "hello_world"
    """
    app_name, method_name = function_name.split("__", 1)
    module_name = f"aipolabs.server.apps.{app_name.lower()}"
    class_name = "".join(word.capitalize() for word in app_name.split("_"))
    method_name = method_name.lower()

    return module_name, class_name, method_name


class AppBase(ABC):
    # TODO: init with end user account credentials

    # TODO: retry?
    def execute(self, function_name: str, args: dict) -> FunctionExecutionResult:
        _, _, method_name = parse_function_name(function_name)
        method = getattr(self, method_name, None)
        if not method:
            logger.error(
                "method not found",
                extra={"method_name": method_name, "class_name": self.__class__.__name__},
            )
            raise NoImplementationFound(
                f"method={method_name} not found in class={self.__class__.__name__}"
            )

        try:
            logger.info(
                "executing method",
                extra={
                    "method_name": method_name,
                    "class_name": self.__class__.__name__,
                    "args": args,
                },
            )
            result = method(**args)
            logger.info(
                "execution result",
                extra={"result": result},
            )
            return FunctionExecutionResult(success=True, data=result)
        except Exception as e:
            logger.exception(
                f"error executing method, {e}",
                extra={
                    "method_name": method_name,
                    "class_name": self.__class__.__name__,
                },
            )
            return FunctionExecutionResult(success=False, error=str(e))

    @staticmethod
    def validate_input(function_parameters_schema: dict, function_input: dict) -> None:
        try:
            validate(instance=function_input, schema=function_parameters_schema)
        except ValidationError as e:
            logger.exception(
                f"function input validation error, {e}",
                extra={
                    "function_input": function_input,
                    "function_parameters_schema": function_parameters_schema,
                },
            )
            raise InvalidFunctionInput(f"invalid function input: {e.message}")


class AppFactory:
    # TODO: caching? singleton per app per enduser account? executing in a thread pool?

    def get_app_instance(self, function_name: str) -> AppBase:

        module_name, class_name, _ = parse_function_name(function_name)

        try:
            app_class: Type[AppBase] = getattr(importlib.import_module(module_name), class_name)
            logger.debug(
                "found app class for function_name",
                extra={"function_name": function_name, "app_class": app_class},
            )
            app_instance: AppBase = app_class()
            return app_instance
        except (ModuleNotFoundError, AttributeError):
            logger.exception(
                f"failed to find app class for function_name={function_name}",
                extra={"function_name": function_name},
            )
            raise NoImplementationFound(
                f"failed to find app class for function_name={function_name}"
            )
