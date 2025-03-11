"""Sanity check function execution with GPT-generated inputs."""

import json
from typing import Any
from uuid import UUID

import click
import httpx
from openai import OpenAI

from aipolabs.cli import config
from aipolabs.common.logging import create_headline
from aipolabs.common.schemas.function import FunctionExecute, InferenceProvider


@click.command()
@click.option(
    "--function-name",
    "function_name",
    required=True,
    type=str,
    help="Name of the function to test",
)
@click.option(
    "--aipolabs-api-key",
    "aipolabs_api_key",
    required=True,
    type=str,
    help="Aipolabs API key to use for authentication",
)
@click.option(
    "--linked-account-owner-id",
    "linked_account_owner_id",
    required=True,
    type=str,
    help="ID of the linked account owner to use for authentication",
)
@click.option(
    "--prompt",
    "prompt",
    type=str,
    help="Prompt for LLM to generate function call arguments",
)
@click.option(
    "--model",
    "model",
    type=str,
    required=False,
    default="gpt-4o-mini",
    help="LLM model to use for function call arguments generation",
)
def fuzzy_test_function_execution(
    aipolabs_api_key: str,
    function_name: str,
    model: str,
    linked_account_owner_id: UUID,
    prompt: str | None = None,
) -> None:
    """Test function execution with GPT-generated inputs."""
    return fuzzy_test_function_execution_helper(
        aipolabs_api_key, function_name, model, linked_account_owner_id, prompt
    )


def fuzzy_test_function_execution_helper(
    aipolabs_api_key: str,
    function_name: str,
    model: str,
    linked_account_owner_id: UUID,
    prompt: str | None = None,
) -> None:
    """Test function execution with GPT-generated inputs."""
    # Get function definition
    response = httpx.get(
        f"{config.SERVER_URL}/v1/functions/{function_name}/definition",
        params={"inference_provider": InferenceProvider.OPENAI.value},
        headers={"x-api-key": aipolabs_api_key},
    )
    if response.status_code != 200:
        raise click.ClickException(f"Failed to get function definition: {response.json()}")

    function_definition = response.json()
    click.echo(create_headline("Function definition fetched"))
    click.echo(f"{json.dumps(function_definition)}")

    # Use OpenAI function calling to generate a random input
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    function_args = _generate_fuzzy_function_call_arguments(
        openai_client, model, function_definition, prompt=prompt
    )
    click.echo(create_headline("Generated function call arguments"))
    click.echo(f"{json.dumps(function_args)}")

    # Execute function with generated input
    function_execute = FunctionExecute(
        function_input=function_args, linked_account_owner_id=str(linked_account_owner_id)
    )
    response = httpx.post(
        f"{config.SERVER_URL}/v1/functions/{function_name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": aipolabs_api_key},
        timeout=30.0,
    )

    if response.status_code != 200:
        raise click.ClickException(f"Function execution failed: {response.json()}")

    result = response.json()
    click.echo(create_headline(f"Execution result for {function_name}"))
    click.echo(f"{json.dumps(result)}")


def _generate_fuzzy_function_call_arguments(
    openai_client: OpenAI,
    model: str,
    function_definition: dict,
    prompt: str | None = None,
) -> Any:
    """
    Generate fuzzy input arguments for a function using GPT-4.
    """
    click.echo(f"Generating fuzzy input for function: {function_definition['function']['name']}")
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
    if prompt:
        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[function_definition],
        tool_choice="required",  # force the model to generate a tool call
    )  # type: ignore

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
