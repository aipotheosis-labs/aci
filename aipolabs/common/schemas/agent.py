from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from aipolabs.common.schemas.apikey import APIKeyPublic

MAX_INSTRUCTION_LENGTH = 5000


# Custom type with validation
def validate_instruction(v: str) -> str:
    if not v.strip():
        raise ValueError("Instructions cannot be empty strings")
    if len(v) > MAX_INSTRUCTION_LENGTH:
        raise ValueError(f"Instructions cannot be longer than {MAX_INSTRUCTION_LENGTH} characters")
    return v


ValidInstruction = Annotated[str, BeforeValidator(validate_instruction)]


def _validate_apps_access_consistency(
    allow_all_apps: bool | None, allowed_apps: list[str] | None
) -> None:
    """Validator function to check allow_all_apps and allowed_apps consistency"""
    if allow_all_apps and allowed_apps:
        raise ValueError("allow_all_apps and allowed_apps cannot be both True and non-empty")


# TODO: validate when creating or updating agent that allowed_apps only contains apps that are configured
# for the project
class AgentCreate(BaseModel):
    name: str
    description: str
    allow_all_apps: bool = True
    allowed_apps: list[str] = []
    custom_instructions: dict[str, ValidInstruction] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_allow_all_apps(self) -> "AgentCreate":
        _validate_apps_access_consistency(self.allow_all_apps, self.allowed_apps)
        return self


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    allow_all_apps: bool | None = None
    allowed_apps: list[str] | None = None
    custom_instructions: dict[str, ValidInstruction] | None = None

    @model_validator(mode="after")
    def check_allow_all_apps(self) -> "AgentUpdate":
        _validate_apps_access_consistency(self.allow_all_apps, self.allowed_apps)
        return self


class AgentPublic(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    allow_all_apps: bool
    allowed_apps: list[str] = []
    custom_instructions: dict[str, ValidInstruction] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime

    api_keys: list[APIKeyPublic]

    model_config = ConfigDict(from_attributes=True)
