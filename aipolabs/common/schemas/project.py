from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aipolabs.common.enums import Visibility
from aipolabs.common.schemas.agent import AgentPublic


class ProjectCreate(BaseModel):
    """Project can be created under a user or an organization."""

    name: str
    organization_id: UUID | None = Field(
        default=None,
        description="Organization ID if project is to be created under an organization",
    )


class ProjectPublic(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    visibility_access: Visibility
    daily_quota_used: int
    daily_quota_reset_at: datetime
    total_quota_used: int

    created_at: datetime
    updated_at: datetime

    agents: list[AgentPublic]

    model_config = ConfigDict(from_attributes=True)
