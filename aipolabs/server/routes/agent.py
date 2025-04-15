from typing import List, Annotated, Literal
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from aipolabs.server import dependencies as deps
from aipolabs.server.agent.prompt import ClientMessage, convert_to_openai_messages, openai_chat_stream
from aipolabs.server.routes.functions import get_functions_definitions
from aipolabs.common.logging_setup import get_logger
from aipolabs.common.enums import FunctionDefinitionFormat
from aipolabs.server import config
from openai import OpenAI

router = APIRouter()
logger = get_logger(__name__)
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

class AgentChat(BaseModel):
    id: str
    linked_account_owner_id: str
    selected_apps: List[str]
    selected_functions: List[str]
    messages: List[ClientMessage]


@router.post("/chat", 
    response_class=StreamingResponse,
    summary="Chat with AI agent",
    description="Handle chat requests and stream responses with tool calling capabilities",
    response_description="Streamed chat completion responses"
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
    logger.info(
        "Processing chat request",
        extra={"project_id": context.project.id}
    )

    openai_messages = convert_to_openai_messages(agent_chat.messages)
    # TODO: support different meta function mode.
    selected_functions = await get_functions_definitions(context.db_session, agent_chat.selected_functions, FunctionDefinitionFormat.OPENAI_RESPONSES)
    logger.info("Selected functions", extra={"functions": [func.model_dump() for func in selected_functions]})
    response = StreamingResponse(openai_chat_stream(openai_messages, tools=selected_functions))
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    
    return response