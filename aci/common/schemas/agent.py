from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from aci.common.schemas.apikey import APIKeyPublic

MAX_INSTRUCTION_LENGTH = 5000


# TODO: add unit tests
# Custom type with validation
def validate_instruction(v: str) -> str:
    if not v.strip():
        raise ValueError("Instructions cannot be empty strings")
    if len(v) > MAX_INSTRUCTION_LENGTH:
        raise ValueError(f"Instructions cannot be longer than {MAX_INSTRUCTION_LENGTH} characters")
    return v


ValidInstruction = Annotated[str, BeforeValidator(validate_instruction)]


# TODO: validate when creating or updating agent that allowed_apps only contains apps that are configured
# for the project
class AgentCreate(BaseModel):
    name: str
    description: str
    allowed_apps: list[str] = []
    custom_instructions: dict[str, ValidInstruction] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    allowed_apps: list[str] | None = None
    custom_instructions: dict[str, ValidInstruction] | None = None


class AgentPublic(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    allowed_apps: list[str] = []
    custom_instructions: dict[str, ValidInstruction] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    api_keys: list[APIKeyPublic]

    model_config = ConfigDict(from_attributes=True)
