from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from aipolabs.common.schemas.apikey import APIKeyPublic


# Custom type with validation
# TODO: add more restrictions like max length, etc?
def validate_instruction(v: str) -> str:
    if not v.strip():
        raise ValueError("Instructions cannot be empty strings")
    return v


ValidInstruction = Annotated[str, BeforeValidator(validate_instruction)]


class AgentCreate(BaseModel):
    name: str
    description: str
    excluded_apps: list[str] = []
    excluded_functions: list[str] = []
    custom_instructions: dict[str, ValidInstruction] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    excluded_apps: list[str] | None = None
    excluded_functions: list[str] | None = None
    custom_instructions: dict[str, ValidInstruction] = Field(default_factory=dict)


class AgentPublic(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    excluded_apps: list[str] = []
    excluded_functions: list[str] = []
    custom_instructions: dict[str, ValidInstruction] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    api_keys: list[APIKeyPublic]

    model_config = ConfigDict(from_attributes=True)
