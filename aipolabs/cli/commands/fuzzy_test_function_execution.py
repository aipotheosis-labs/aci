"""Sanity check function execution with GPT-generated inputs."""

import json
from uuid import UUID

import click
import httpx

from aipolabs.cli import config
from aipolabs.common.logging import create_headline
from aipolabs.common.openai_service import OpenAIService
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
def fuzzy_test_function_execution(
    aipolabs_api_key: str,
    function_name: str,
    linked_account_owner_id: UUID,
    prompt: str | None = None,
) -> None:
    """Test function execution with GPT-generated inputs."""
    return fuzzy_test_function_execution_helper(
        aipolabs_api_key, function_name, linked_account_owner_id, prompt
    )


def fuzzy_test_function_execution_helper(
    aipolabs_api_key: str,
    function_name: str,
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
    openai_service = OpenAIService(config.OPENAI_API_KEY)
    function_args = openai_service.generate_fuzzy_function_call_arguments(
        function_definition, prompt=prompt
    )
    click.echo(create_headline("Generated function call arguments"))
    click.echo(f"{json.dumps(function_args)}")

    # Execute function with generated input
    function_execute = FunctionExecute(
        function_input=function_args, linked_account_owner_id=linked_account_owner_id
    )
    response = httpx.post(
        f"{config.SERVER_URL}/v1/functions/{function_name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": aipolabs_api_key},
    )

    if response.status_code != 200:
        raise click.ClickException(f"Function execution failed: {response.json()}")

    result = response.json()
    click.echo(create_headline(f"Execution result for {function_name}"))
    click.echo(f"{json.dumps(result)}")
