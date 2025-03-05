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
) -> FilterResponse:
    args = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that looks at a function call and a custom instruction, then determines whether the function should be executed."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Decide if the function call should be allowed or not based on the rule, function definition, and input. "
                    f"Function name: {function.name}, "
                    f"Function description: {function.description}, "
                    f"Custom instruction: {custom_instructions},"
                    f"Function input: {function_input}"
                ),
            },
        ],
        "temperature": 0,
    }

    # TODO: abstract out to InferenceService
    # - make an inference layer to handle embeddings, filtering, rag etc
    return openai_service.get_structured_response(response_format=FilterResponse, **args)
