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
CustomInstructions = dict[UUID, ValidInstruction]


class AgentCreate(BaseModel):
    name: str
    description: str
    excluded_apps: list[UUID] = []
    excluded_functions: list[UUID] = []
    custom_instructions: CustomInstructions = Field(default_factory=dict)
    model_config = ConfigDict(json_encoders={UUID: str})


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    excluded_apps: list[UUID] | None = None
    excluded_functions: list[UUID] | None = None
    custom_instructions: CustomInstructions = Field(default_factory=dict)
    model_config = ConfigDict(json_encoders={UUID: str})


class AgentPublic(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    excluded_apps: list[UUID] = []
    excluded_functions: list[UUID] = []
    custom_instructions: CustomInstructions = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    api_keys: list[APIKeyPublic]

    model_config = ConfigDict(from_attributes=True, json_encoders={UUID: str})
