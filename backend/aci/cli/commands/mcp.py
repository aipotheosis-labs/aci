import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, cast

import click
import httpx
from rich import print as rprint
from rich.console import Console

console = Console()

MCP_PROTOCOL_VERSION = "2025-06-18"


def _validate_app_name(ctx: click.Context, param: click.Parameter, value: str) -> str:
    """Validate that app name only contains uppercase letters, numbers, underscores and no consecutive underscores"""
    if not value:
        return value

    # Check if contains only valid characters (uppercase letters, numbers, underscores)
    if not re.match(r"^[A-Z0-9_]+$", value):
        raise click.BadParameter(
            "App name must contain only uppercase letters (A-Z), numbers (0-9), and underscores (_). "
            f"Invalid characters found in: {value}"
        )

    # Check for consecutive underscores
    if "__" in value:
        raise click.BadParameter(
            f"App name cannot contain consecutive underscores. Found in: {value}"
        )

    # Check if starts or ends with underscore
    if value.startswith("_") or value.endswith("_"):
        raise click.BadParameter(f"App name cannot start or end with underscore. Found: {value}")

    return value


@click.command()
@click.option(
    "--app-name",
    required=True,
    callback=_validate_app_name,
    help="App name to be used as prefix for function names, e.g., NOTION, NOTION_V2. Must contain only uppercase letters, numbers, and underscores (no consecutive underscores).",
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

    # Create final report
    summary = {
        "app_name": app_name,
        "mcp_server_url": mcp_server_url,
        "security_scheme": "oauth2",
        "need_initialize": need_initialize,
        "initialize_latency": round(initialize_latency, 3),
        "mcp_session_id_example (if present)": mcp_session_id,
        "number_of_tools": len(tools),
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
        function_name = f"{app_name}__{_sanitize_orginal_tool_name(tool['name'])}"

        rprint(f"Creating function {function_name} (mcp tool name: {tool['name']})")

        # Check description length
        description = tool["description"]
        if len(description) > 1024:
            rprint(
                f"  └─ [yellow]Warning: Description for '{tool['name']}' is {len(description)} characters (exceeds 1024 limit). Need manual fix after generation.[/yellow]"
            )

        # Generate hashes for change detection
        description_hash = _normalize_and_hash_content(description)
        input_schema_hash = _normalize_and_hash_content(tool["inputSchema"])

        # Build function definition according to the specification
        function = {
            "name": function_name,
            "description": description,
            "tags": [],
            "visibility": "public",
            "active": True,
            "protocol": "mcp",
            "protocol_data": {
                "original_tool_name": tool["name"],
                # storing hashes so we can better detect changes from the original MCP server
                "original_tool_description_hash": description_hash,
                "original_tool_input_schema_hash": input_schema_hash,
                "need_initialize": need_initialize,
            },
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


def _parse_mcp_response(response: httpx.Response) -> Any:
    """Parse MCP response, handling both JSON and event-stream formats"""
    content_type = response.headers.get("content-type", "").lower()

    if "text/event-stream" in content_type:
        content = response.text.strip()
        lines = content.split("\n")

        # Find the data line in event-stream format
        for line in lines:
            if line.startswith("data:"):
                # Extract JSON from "data: {...}"
                json_str = line[5:].strip()  # Remove "data:" prefix
                if json_str:
                    return json.loads(json_str)

        raise click.ClickException("No valid JSON data found in SSE response")
    else:
        # Regular JSON response
        return response.json()


def _normalize_and_hash_content(content: Any) -> str:
    """
    Normalize content and generate a hash to detect meaningful changes while ignoring formatting.

    For strings: keeps only letters and numbers (removes punctuation, whitespace, etc.)
    For objects: converts to normalized JSON with sorted keys
    """
    if isinstance(content, str):
        # Normalize string content:
        # 1. Convert to lowercase for case-insensitive comparison
        # 2. Keep only letters and numbers (remove all punctuation, whitespace, etc.)
        normalized = re.sub(r"[^a-z0-9]", "", content.lower())
    else:
        # For objects (like inputSchema), convert to normalized JSON
        # Sort keys to ensure consistent ordering
        normalized = json.dumps(content, sort_keys=True, separators=(",", ":"))

    # Generate SHA-256 hash of normalized content
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _sanitize_orginal_tool_name(original_tool_name: str) -> str:
    """Convert MCP tool name to comply with naming rules: uppercase letters, numbers, underscores only, no consecutive underscores"""
    if not original_tool_name:
        return original_tool_name

    # Convert to uppercase
    sanitized = original_tool_name.upper()

    # Replace any non-alphanumeric characters (except underscores) with underscores
    sanitized = re.sub(r"[^A-Z0-9_]", "_", sanitized)

    # Remove consecutive underscores by replacing multiple underscores with single underscore
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading and trailing underscores
    sanitized = sanitized.strip("_")

    # If the sanitized name is empty (edge case), provide a fallback
    if not sanitized:
        rprint(
            f"[yellow]Warning: Tool name '{original_tool_name}' is empty after sanitization. Using 'UNKNOWN_TOOL' as placeholder. Need manual fix after generation.[/yellow]"
        )
        sanitized = "UNKNOWN_TOOL"

    return sanitized
