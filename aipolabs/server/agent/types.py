from pydantic import BaseModel, Field


class ToolInvocation(BaseModel):
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    step: int
    state: str | None = None
    args: dict | None = None
    result: dict | list[dict] | None = None


class ClientMessage(BaseModel):
    role: str
    content: str
    tool_invocations: list[ToolInvocation] | None = Field(default=None, alias="toolInvocations")
