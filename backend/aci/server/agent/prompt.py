# mypy: ignore-errors
import json

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from aci.common.logging_setup import get_logger
from aci.common.schemas.function import OpenAIResponsesFunctionDefinition
from aci.server import config

from .types import ClientMessage

logger = get_logger(__name__)


def convert_to_openai_messages(messages: list[ClientMessage]) -> list[ChatCompletionMessageParam]:
    """
    Convert a list of ClientMessage objects to a list of OpenAI messages.

    Args:
        messages: A list of ClientMessage objects

    Returns:
        A list of OpenAI messages
    """
    openai_messages = []

    for message in messages:
        if message.tool_invocations:
            # Convert ToolInvocation objects to dictionaries before adding them
            for ti in message.tool_invocations:
                openai_messages.append(
                    {
                        "type": "function_call",
                        "call_id": ti.tool_call_id,
                        "name": ti.tool_name,
                        "arguments": json.dumps(ti.args),
                    }
                )
                if ti.result:
                    openai_messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": ti.tool_call_id,
                            "output": json.dumps(ti.result),
                        }
                    )
            continue
        else:
            content = []
            content.append(
                {
                    "type": "input_text" if message.role == "user" else "output_text",
                    "text": message.content,
                }
            )
            openai_messages.append({"role": message.role, "type": "message", "content": content})

    return openai_messages


async def openai_chat_stream(
    messages: list[ChatCompletionMessageParam],
    tools: list[OpenAIResponsesFunctionDefinition],
):
    """
    Stream chat completion responses and handle tool calls asynchronously.

    Args:
        messages: List of chat messages
        tools: List of tools to use
    """
    logger.info("Messages", extra={"messages": json.dumps(messages)})
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    # TODO: support different meta function mode ACI_META_FUNCTIONS_SCHEMA_LIST
    stream = client.responses.create(model="gpt-4o", input=messages, stream=True, tools=tools)

    for event in stream:
        final_tool_calls = {}

        for event in stream:
            if event.type == "response.output_text.delta":
                # Stream text content
                if event.delta:
                    yield f"0:{json.dumps(event.delta)}\n"

            elif event.type == "response.output_item.added":
                final_tool_calls[event.output_index] = event.item

            elif event.type == "response.function_call_arguments.delta":
                index = event.output_index
                if final_tool_calls[index]:
                    final_tool_calls[index].arguments += event.delta

            elif event.type == "response.function_call_arguments.done":
                # Emit completed tool call
                index = event.output_index
                if final_tool_calls[index]:
                    tool_call = final_tool_calls[index]

                    yield f'9:{{"toolCallId":"{tool_call.call_id}","toolName":"{tool_call.name}","args":{tool_call.arguments}}}\n'
                    logger.info("Tool_call_id", extra={"tool_call_id": tool_call.call_id})
                    logger.info("Tool_id", extra={"tool_id": tool_call.id})

            elif event.type == "response.completed":
                if hasattr(event, "usage"):
                    yield 'd:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}}}}\n'.format(
                        reason="tool-calls" if final_tool_calls else "stop",
                        prompt=event.usage.prompt_tokens,
                        completion=event.usage.completion_tokens,
                    )
