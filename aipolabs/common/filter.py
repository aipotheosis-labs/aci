from typing import Any

from aipolabs.common.db.sql_models import Function
from aipolabs.common.logging import get_logger
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.function import FilterResponse

logger = get_logger(__name__)


def filter_function_call(
    openai_service: OpenAIService,
    function: Function,
    function_input: dict,
    custom_instructions: str,
) -> Any:

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that decides if a function call should be allowed or not based on a rule, function definition, and input."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Decide if the function call should be allowed or not based on the rule, function definition, and input. "
                f"Function Definition: {function.name}, "
                f"Function Description: {function.description}, "
                f"Function Parameters: {function.parameters}, "
                f"Function Input: {function_input},"
                f"Rule: {custom_instructions}"
            ),
        },
    ]
    # TODO: abstract out to InferenceService
    # - make an inference layer to handle embeddings, filtering, rag etc
    # - bad to have business logic inside openai_service
    return openai_service.filter(messages, FilterResponse)
