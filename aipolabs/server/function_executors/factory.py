from aipolabs.common.enums import Protocol
from aipolabs.server.function_executors.base_executor import FunctionExecutor
from aipolabs.server.function_executors.rest_function_executor import (
    RestFunctionExecutor,
)


def get_executor(protocol: Protocol) -> FunctionExecutor:
    if protocol == Protocol.REST:
        return RestFunctionExecutor()
    else:
        raise ValueError(f"Unsupported protocol={protocol}")
