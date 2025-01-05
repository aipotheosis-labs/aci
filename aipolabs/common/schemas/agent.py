from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aipolabs.common.schemas.apikey import APIKeyPublic


class AgentCreate(BaseModel):
    name: str
    description: str
    excluded_apps: list[UUID] = []
    excluded_functions: list[UUID] = []


class AgentPublic(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    excluded_apps: list[UUID] = []
    excluded_functions: list[UUID] = []

    created_at: datetime
    updated_at: datetime

    api_keys: list[APIKeyPublic]

    model_config = ConfigDict(from_attributes=True)
