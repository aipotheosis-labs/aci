"""Sanity check function execution with GPT-generated inputs."""

import json
from typing import Any
from uuid import UUID

import click
import httpx
from openai import OpenAI
from rich.console import Console

from aci.cli import config
from aci.common.enums import FunctionDefinitionFormat
from aci.common.schemas.function import FunctionExecute

console = Console()


@click.command()
@click.option(
    "--function-name",
    "function_name",
    required=True,
    type=str,
    help="Name of the function to test",
)
@click.option(
    "--aci-api-key",
    "aci_api_key",
    required=True,
    type=str,
    help="ACI API key to use for authentication",
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
    default="gpt-4o",
    help="LLM model to use for function call arguments generation",
)
def fuzzy_test_function_execution(
    aci_api_key: str,
    function_name: str,
    model: str,
    linked_account_owner_id: UUID,
    prompt: str | None = None,
) -> None:
    """Test function execution with GPT-generated inputs."""
    return fuzzy_test_function_execution_helper(
        aci_api_key, function_name, model, linked_account_owner_id, prompt
    )


def fuzzy_test_function_execution_helper(
    aci_api_key: str,
    function_name: str,
    model: str,
    linked_account_owner_id: UUID,
    prompt: str | None = None,
) -> None:
    """Test function execution with GPT-generated inputs."""
    # Get function definition
    response = httpx.get(
        f"{config.SERVER_URL}/v1/functions/{function_name}/definition",
        params={"format": FunctionDefinitionFormat.OPENAI},
        headers={"x-api-key": aci_api_key},
    )
    if response.status_code != 200:
        raise click.ClickException(f"Failed to get function definition: {response.json()}")

    function_definition = response.json()
    console.rule("[bold green]Function definition Fetched[/bold green]")
    console.print(function_definition)

    # Use OpenAI function calling to generate a random input
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    function_args = _generate_fuzzy_function_call_arguments(
        openai_client, model, function_definition, prompt=prompt
    )
    console.rule("[bold green]Generated Function Call Arguments[/bold green]")
    console.print(function_args)

    # Execute function with generated input
    function_execute = FunctionExecute(
        function_input=function_args, linked_account_owner_id=str(linked_account_owner_id)
    )
    response = httpx.post(
        f"{config.SERVER_URL}/v1/functions/{function_name}/execute",
        json=function_execute.model_dump(mode="json"),
        headers={"x-api-key": aci_api_key},
        timeout=30.0,
    )

    if response.status_code != 200:
        raise click.ClickException(f"Function execution failed: {response.json()}")

    result = response.json()
    console.rule(f"[bold green]Execution Result for {function_name}[/bold green]")
    console.print(result)


def _generate_fuzzy_function_call_arguments(
    openai_client: OpenAI,
    model: str,
    function_definition: dict,
    prompt: str | None = None,
) -> Any:
    """
    Generate fuzzy input arguments for a function with LLM.
    """
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
            console.print(
                f"[bold red]Generated function name {tool_call.function.name} does not match expected function name {function_definition['function']['name']}[/bold red]"
            )
            raise click.ClickException(
                "Generated function name does not match expected function name"
            )
        else:
            return json.loads(tool_call.function.arguments)
    else:
        console.print("[bold red]No tool call was generated[/bold red]")
        raise click.ClickException("No tool call was generated")
