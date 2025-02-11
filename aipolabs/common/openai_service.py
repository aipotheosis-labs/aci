import json
from typing import Any, Type, TypeVar, cast

from openai import OpenAI
from pydantic import BaseModel

from aipolabs.common.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


# TODO: if multiple concurrent requests, would this be a bottleneck and potentially banned?
# TODO: backup plan if OpenAI is down?
# TODO: should this be a singleton and inject into routes? and use a thread pool to handle concurrent requests?
class OpenAIService:
    def __init__(
        self,
        api_key: str,
    ) -> None:
        self.openai_client = OpenAI(api_key=api_key)

    # TODO: exponential backoff?
    def generate_embedding(
        self, text: str, embedding_model: str, embedding_dimension: int
    ) -> list[float]:
        """
        Generate an embedding for the given text using OpenAI's model.
        """
        logger.debug(f"Generating embedding for text: {text}")
        try:
            response = self.openai_client.embeddings.create(
                input=[text],
                model=embedding_model,
                dimensions=embedding_dimension,
            )
            embedding: list[float] = response.data[0].embedding
            return embedding
        except Exception:
            logger.error("Error generating embedding", exc_info=True)
            raise

    def generate_fuzzy_function_call_arguments(
        self, function_definition: dict, chat_model: str = "gpt-4o-mini"
    ) -> Any:
        """
        Generate fuzzy input arguments for a function using GPT-4.
        """
        logger.info(
            f"Generating fuzzy input for function: {function_definition['function']['name']}"
        )
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates test inputs for API functions. Generate reasonable test values that would work with the function.",
            },
            {
                "role": "user",
                "content": f"Generate test input for this function {function_definition['function']['name']}, definition provided to you separately.",
            },
        ]

        response = self.openai_client.chat.completions.create(
            model=chat_model,
            messages=messages,
            tools=[function_definition],
            tool_choice="required",  # force the model to generate a tool call
        )

        tool_call = (
            response.choices[0].message.tool_calls[0]
            if response.choices[0].message.tool_calls
            else None
        )
        if tool_call:
            if tool_call.function.name != function_definition["function"]["name"]:
                raise ValueError(
                    f"Generated function name {tool_call.function.name} does not match expected function name {function_definition['function']['name']}"
                )
            else:
                return json.loads(tool_call.function.arguments)
        else:
            raise ValueError("No tool call was generated")

    # TODO: note this is a beta feature from OpenAI
    def get_structured_response(self, response_format: Type[T], **kwargs: Any) -> T:
        """Returns a structured response from OpenAI API"""
        kwargs["response_format"] = response_format
        response = self.openai_client.beta.chat.completions.parse(**kwargs)
        return cast(T, response.choices[0].message.parsed)
