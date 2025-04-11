import json
from openai import OpenAI
from aipolabs.server import config
from pydantic import BaseModel
from typing import List, Optional
from .types import ToolInvocation
from openai.types.chat import ChatCompletionMessageParam
from aipolabs.common.logging_setup import get_logger
from aipolabs.server.routes.functions import execute_function
logger = get_logger(__name__)

class ClientMessage(BaseModel):
    role: str
    content: str
    toolInvocations: Optional[List[ToolInvocation]] = None


def convert_to_openai_messages(messages: List[ClientMessage]) -> List[ChatCompletionMessageParam]:
    """
    Convert a list of ClientMessage objects to a list of OpenAI messages.

    Args:
        messages: A list of ClientMessage objects

    Returns:
        A list of OpenAI messages
    """
    openai_messages = []

    for message in messages:
        if message.toolInvocations:
            
            # Convert ToolInvocation objects to dictionaries before adding them
            for ti in message.toolInvocations:
                openai_messages.append({
                    "type": "function_call",
                    "call_id": ti.toolCallId,
                    "name": ti.toolName,
                    "arguments": json.dumps(ti.args)
                })
                if ti.result:
                    openai_messages.append({
                        "type": "function_call_output",
                        "call_id": ti.toolCallId,
                        "output": json.dumps(ti.result)
                    })
            continue
        else:
            content = []
            content.append({
                'type': 'input_text' if message.role == 'user' else 'output_text',
                'text': message.content
            })
            openai_messages.append({
                "role": message.role,
                "type": "message",
                "content": content
            })

    return openai_messages


async def openai_chat_stream_text(messages: List[ChatCompletionMessageParam], protocol: str = 'data', tools=None):
    """
    Stream chat completion responses and handle tool calls asynchronously.
    
    Args:
        messages: List of chat messages
        protocol: Protocol type for streaming response format
        tools: List of tool definitions to use for function calling
        linked_account_owner_id: Linked account owner id
    """
    logger.info(
        "Messages",
        extra={"messages": json.dumps(messages)}
    )
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    stream = client.responses.create(
        model="gpt-4o",
        input=messages,
        stream=True,
        tools=tools
    )

    for event in stream:
        if protocol == 'data':
            final_tool_calls = {}

            for event in stream:
                if event.type == 'response.output_text.delta':
                    # Stream text content
                    if event.delta:
                        yield '0:{text}\n'.format(text=json.dumps(event.delta))

                elif event.type == 'response.output_item.added':
                    final_tool_calls[event.output_index] = event.item

                elif event.type == 'response.function_call_arguments.delta':
                    index = event.output_index
                    if final_tool_calls[index]:
                        final_tool_calls[index].arguments += event.delta

                elif event.type == 'response.function_call_arguments.done':
                    # Emit completed tool call
                    index = event.output_index
                    if final_tool_calls[index]:
                        tool_call = final_tool_calls[index]

                        yield '9:{{"toolCallId":"{call_id}","toolName":"{name}","args":{args}}}\n'.format(
                            call_id=tool_call.call_id,
                            name=tool_call.name,
                            args=tool_call.arguments
                        )
                        logger.info(
                            "Tool_call_id",
                            extra={"tool_call_id": tool_call.call_id}
                        )
                        logger.info(
                            "Tool_id",
                            extra={"tool_id": tool_call.id}
                        )

                elif event.type == 'response.completed':
                    if hasattr(event, 'usage'):
                        yield 'd:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}}}}\n'.format(
                            reason="tool-calls" if final_tool_calls else "stop",
                            prompt=event.usage.prompt_tokens,
                            completion=event.usage.completion_tokens
                        )