import json
import re
import time
from pathlib import Path
from typing import cast

import click
import httpx
from rich import print as rprint
from rich.console import Console

console = Console()

MCP_PROTOCOL_VERSION = "2025-06-18"


@click.command()
@click.option(
    "--app-name",
    required=True,
    help="App name to be used as prefix for function names, e.g., NOTION, NOTION_V2",
)
@click.option(
    "--mcp-server-url",
    type=str,
    required=True,
    help="MCP server URL, e.g., https://mcp.notion.com/mcp",
)
@click.option(
    "--security-scheme",
    type=click.Choice(["oauth2", "api-key", "no-auth"], case_sensitive=False),
    required=True,
    help="Authentication method to use",
)
@click.option(
    "--access-token", help="Access token for OAuth2 authentication (required when auth=oauth2)"
)
@click.option(
    "--api-key-header",
    help="Header name for API key authentication (e.g., X-API-KEY, required when auth=api-key)",
)
@click.option("--api-key-value", help="API key value (required when auth=api-key)")
def generate_functions_file_from_mcp_server(
    mcp_server_url: str,
    security_scheme: str,
    access_token: str | None,
    api_key_header: str | None,
    api_key_value: str | None,
    app_name: str,
) -> None:
    match security_scheme:
        case "oauth2":
            if not access_token:
                raise click.BadParameter("--access-token is required for OAuth2 authentication")
            return handle_oauth2_mcp_server(app_name, mcp_server_url, access_token)
        case _:
            raise click.BadParameter(f"Unsupported security scheme: {security_scheme}")


def handle_oauth2_mcp_server(app_name: str, mcp_server_url: str, access_token: str) -> None:
    console.rule(f"Starting MCP server analysis for {mcp_server_url}")

    # Check if initialize is required
    initialize_start = time.perf_counter()
    need_initialize = _check_if_initialize_is_required(mcp_server_url, access_token)
    initialize_latency = time.perf_counter() - initialize_start if need_initialize else 0

    # Initialize session if needed
    mcp_session_id = None
    if need_initialize:
        init_start = time.perf_counter()
        mcp_session_id = _initialize(mcp_server_url, access_token)
        initialize_latency = time.perf_counter() - init_start

    # List tools
    list_tools_start = time.perf_counter()
    tools = _list_tools(mcp_server_url, access_token, mcp_session_id)
    list_tools_latency = time.perf_counter() - list_tools_start

    number_of_tools = len(tools)
    if tools:
        console.print(json.dumps(tools[0], indent=2))
    else:
        console.print("No tools found")
    # Create final report
    summary = {
        "app_name": app_name,
        "mcp_server_url": mcp_server_url,
        "security_scheme": "oauth2",
        "need_initialize": need_initialize,
        "initialize_latency": round(initialize_latency, 3),
        "mcp_session_id_example (if present)": mcp_session_id,
        "number_of_tools": number_of_tools,
        "list_tools_latency": round(list_tools_latency, 3),
    }

    console.rule(f"MCP server analysis for {app_name}")
    console.print(summary)

    # Create function file
    console.rule(f"Creating functions.json file for {app_name}")
    _create_function_file(app_name, tools, need_initialize)


# Even though MCP spec require initialize, some MCP legacy server might not support it
def _check_if_initialize_is_required(mcp_server_url: str, access_token: str) -> bool:
    rprint("[bold cyan]Checking if initialize is required[/bold cyan]")
    try:
        _list_tools(mcp_server_url, access_token)
        rprint("  └─ [green]Initialize is not required[/green]")
        return False
    except httpx.HTTPStatusError:
        rprint("  └─ [yellow]Initialize is required[/yellow]")
        return True


def _initialize(mcp_server_url: str, access_token: str) -> str | None:
    """Initialize MCP session using JSON-RPC 2.0"""
    rprint("[bold cyan]Initializing MCP session[/bold cyan]")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    # JSON-RPC 2.0 payload for initialize
    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"roots": {}, "sampling": {}},
            "clientInfo": {"name": "ACI", "version": "0.1.0"},
        },
        "id": 1,
    }

    with httpx.Client() as client:
        response = client.post(mcp_server_url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()

        # Parse response based on content type
        data = _parse_mcp_response(response)

        # Check for JSON-RPC errors
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            rprint(f"  └─ [red]Error: {error_msg}[/red]")
            raise click.ClickException(f"MCP server initialization error: {error_msg}")

        # some server returns a mcp-session-id in response headers
        session_id: str | None = response.headers.get("mcp-session-id")
        if session_id:
            rprint(f"  └─ [green]Session established: {session_id}[/green]")
        else:
            rprint("  └─ [green]Session established (no session ID returned)[/green]")

        return session_id


# TODO: handle pagination
def _list_tools(
    mcp_server_url: str, access_token: str, mcp_session_id: str | None = None
) -> list[dict]:
    """List tools from MCP server using JSON-RPC 2.0"""
    rprint("[bold cyan]Listing tools[/bold cyan]")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    # Add optional mcp-session-id header if provided
    if mcp_session_id:
        headers["mcp-session-id"] = mcp_session_id

    # JSON-RPC 2.0 payload
    payload = {"jsonrpc": "2.0", "method": "tools/list", "id": 2}

    with httpx.Client() as client:
        response = client.post(mcp_server_url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()

        # Parse response based on content type
        data = _parse_mcp_response(response)

        # Check for JSON-RPC errors
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            raise click.ClickException(f"MCP server error: {error_msg}")

        # Extract tools from result
        if "result" not in data:
            raise click.ClickException("Invalid JSON-RPC response: missing result")

        result = data["result"]
        if "tools" not in result:
            raise click.ClickException("Invalid response: missing tools in result")

        return cast(list[dict], result["tools"])


def _create_function_file(app_name: str, tools: list[dict], need_initialize: bool) -> None:
    """Generate JSON schemas for function definitions and save to functions.json"""
    functions = []

    for tool in tools:
        # Generate function name: {app_name}_{tool_name} (all uppercase)
        # Convert any non-alphanumeric characters (except underscores) to underscores
        raw_function_name = f"{app_name}__{tool['name']}".upper()
        function_name = re.sub(r"[^A-Z0-9_]", "_", raw_function_name)

        # Print function name and original tool name
        rprint(f"Creating function {function_name} (mcp tool name: {tool['name']})")

        if "__" in function_name:
            rprint(
                f"  └─ [yellow]Warning: Function name '{function_name}' contains consecutive underscores. Need manual fix after generation.[/yellow]"
            )

        # Check description length
        description = tool["description"]
        if len(description) > 1024:
            rprint(
                f"  └─ [yellow]Warning: Description for '{tool['name']}' is {len(description)} characters (exceeds 1024 limit). Need manual fix after generation.[/yellow]"
            )

        # Build function definition according to the specification
        function = {
            "name": function_name,
            "description": description,
            "tags": [],
            "visibility": "public",
            "active": True,
            "protocol": "mcp",
            "protocol_data": {"mcp_tool_name": tool["name"], "need_initialize": need_initialize},
            "parameters": tool["inputSchema"],
        }

        functions.append(function)

    # Write functions to functions.json file in the corresponding app folder
    output_dir = Path("apps") / app_name.lower()

    # Create app folder if it doesn't exist
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        rprint(f"[blue]Created app directory: {output_dir}[/blue]")

    functions_file = output_dir / "functions.json"

    with open(functions_file, "w") as f:
        json.dump(functions, f, indent=2)

    rprint(f"[green]Created functions.json with {len(functions)} functions[/green]")
    rprint(f"[green]Local path: ./apps/{app_name.lower()}/functions.json[/green]")


def _parse_mcp_response(response: httpx.Response) -> dict:
    """Parse MCP response, handling both JSON and event-stream formats"""
    content_type = response.headers.get("content-type", "").lower()

    if "text/event-stream" in content_type:
        # TODO:Parse event-stream format?
        # content = response.text.strip()
        # lines = content.split("\n")

        # # Find the data line in event-stream format
        # for line in lines:
        #     if line.startswith("data:"):
        #         # Extract JSON from "data: {...}"
        #         json_str = line[5:].strip()  # Remove "data:" prefix
        #         if json_str:
        #             return json.loads(json_str)

        # raise click.ClickException("No valid JSON data found in SSE response")
        raise click.ClickException("text/event-stream responses are not supported yet")
    else:
        # Regular JSON response
        return cast(dict, response.json())
