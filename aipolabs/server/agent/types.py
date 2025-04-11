from pydantic import BaseModel

class ToolInvocation(BaseModel):
    toolCallId: str
    toolName: str
    step: int
    state: str | None = None
    args: dict | None = None
    result: dict | None = None