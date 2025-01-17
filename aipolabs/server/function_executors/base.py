import json
from abc import ABC, abstractmethod

import jsonschema

from aipolabs.common import processor
from aipolabs.common.db.sql_models import Function, LinkedAccount
from aipolabs.common.enums import Protocol
from aipolabs.common.exceptions import InvalidFunctionInput
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.function import FunctionExecutionResult
from aipolabs.server.function_executors.rest_function_executor import (
    RestFunctionExecutor,
)

logger = get_logger(__name__)


class FunctionExecutor(ABC):
    """
    Base class for function executors.
    """

    @classmethod
    def get_executor(cls, protocol: Protocol) -> "FunctionExecutor":
        if protocol == Protocol.REST:
            return RestFunctionExecutor()
        else:
            raise ValueError(f"Unsupported protocol={protocol}")

    # TODO: allow local code execution override by using AppBase.execute() e.g.,:
    # app_factory = AppFactory()
    # app_instance: AppBase = app_factory.get_app_instance(function_name)
    # app_instance.validate_input(function.parameters, function_execution_params.function_input)
    # return app_instance.execute(function_name, function_execution_params.function_input)
    def execute(
        self, function: Function, function_input: dict, linked_account: LinkedAccount
    ) -> FunctionExecutionResult:
        """
        Execute the function based on end-user input and end-user linked account.
        Input validation, default values injection, and security credentials injection are done here.
        """
        logger.info(
            f"executing function={function.id}, function_name={function.name}, "
            f"function_input={function_input}, linked_account_owner_id={linked_account.linked_account_owner_id}"
        )
        function_input = self._preprocess_function_input(function, function_input)

        return self._execute(function, function_input, linked_account)

    def _preprocess_function_input(self, function: Function, function_input: dict) -> dict:
        # validate user input against the "visible" parameters
        try:
            jsonschema.validate(
                instance=function_input,
                schema=processor.filter_visible_properties(function.parameters),
            )
        except jsonschema.ValidationError as e:
            logger.exception(f"failed to validate function input for function={function.id}")
            raise InvalidFunctionInput(e.message)

        logger.info(f"function_input before injecting defaults: {json.dumps(function_input)}")

        # inject non-visible defaults, note that should pass the original parameters schema not just visible ones
        function_input = processor.inject_required_but_invisible_defaults(
            function.parameters, function_input
        )
        logger.info(f"function_input after injecting defaults: {json.dumps(function_input)}")

        # remove None values from the input
        # TODO: better way to remove None values? and if it's ok to remove all of them?
        function_input = processor.remove_none_values(function_input)

        return function_input

    @abstractmethod
    def _execute(
        self, function: Function, function_input: dict, linked_account: LinkedAccount
    ) -> FunctionExecutionResult:
        pass
