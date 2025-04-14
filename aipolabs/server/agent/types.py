from pydantic import BaseModel
from typing import List

class ToolInvocation(BaseModel):
    toolCallId: str
    toolName: str
    step: int
    state: str | None = None
    args: dict | None = None
    result: dict | List[dict] | None = None