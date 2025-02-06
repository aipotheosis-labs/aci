from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pydantic.functional_serializers import PlainSerializer

from aipolabs.common.schemas.apikey import APIKeyPublic


# Custom type with validation
# TODO: add more restrictions like max length, etc?
def validate_instruction(v: str) -> str:
    if not v.strip():
        raise ValueError("Instructions cannot be empty strings")
    return v


ValidInstruction = Annotated[str, BeforeValidator(validate_instruction)]
SerializedUUID = Annotated[
    UUID, PlainSerializer(lambda x: str(x), return_type=str, when_used="json")
]
CustomInstructions = dict[SerializedUUID, ValidInstruction]


class AgentCreate(BaseModel):
    name: str
    description: str
    excluded_apps: list[UUID] = []
    excluded_functions: list[UUID] = []
    custom_instructions: CustomInstructions = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    excluded_apps: list[UUID] | None = None
    excluded_functions: list[UUID] | None = None
    custom_instructions: CustomInstructions = Field(default_factory=dict)


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

    model_config = ConfigDict(from_attributes=True)
