from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from aci.common.enums import FunctionDefinitionFormat
from aci.common.logging_setup import get_logger
from aci.common.schemas.function import OpenAIResponsesFunctionDefinition
from aci.server import config
from aci.server import dependencies as deps
from aci.server.agent.prompt import (
    ClientMessage,
    convert_to_openai_messages,
    openai_chat_stream,
)
from aci.server.routes.functions import get_functions_definitions

router = APIRouter()
logger = get_logger(__name__)
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)


class AgentChat(BaseModel):
    id: str
    linked_account_owner_id: str
    selected_apps: list[str]
    selected_functions: list[str]
    messages: list[ClientMessage]


@router.post(
    "/chat",
    response_class=StreamingResponse,
    summary="Chat with AI agent",
    description="Handle chat requests and stream responses with tool calling capabilities",
    response_description="Streamed chat completion responses",
)
async def handle_chat(
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
    agent_chat: AgentChat,
) -> StreamingResponse:
    """
    Handle chat requests and stream responses.

    Args:
        context: Request context with authentication and project info
        agent_chat: Chat request containing messages and function information

    Returns:
        StreamingResponse: Streamed chat completion responses
    """
    logger.info("Processing chat request", extra={"project_id": context.project.id})

    openai_messages = convert_to_openai_messages(agent_chat.messages)
    # TODO: support different meta function mode.
    selected_functions = await get_functions_definitions(
        context.db_session, agent_chat.selected_functions, FunctionDefinitionFormat.OPENAI_RESPONSES
    )
    logger.info(
        "Selected functions",
        extra={"functions": [func.model_dump() for func in selected_functions]},
    )

    tools = [
        func for func in selected_functions if isinstance(func, OpenAIResponsesFunctionDefinition)
    ]

    response = StreamingResponse(openai_chat_stream(openai_messages, tools=tools))
    response.headers["x-vercel-ai-data-stream"] = "v1"

    return response
