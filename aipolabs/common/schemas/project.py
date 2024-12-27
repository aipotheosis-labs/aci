from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aipolabs.common.enums import ProjectOwnerType
from aipolabs.common.schemas.agent import AgentPublic


class ProjectCreate(BaseModel):
    """Project can be created under a user or an organization."""

    name: str
    owner_type: ProjectOwnerType
    owner_id: UUID
    # creator of the project, should be a user and should be the same as owner_id if owner_type is user
    created_by: UUID


class ProjectPublic(BaseModel):
    id: UUID
    name: str
    owner_user_id: UUID | None = None
    owner_organization_id: UUID | None = None
    daily_quota_used: int
    daily_quota_reset_at: datetime
    total_quota_used: int

    created_at: datetime
    updated_at: datetime

    agents: list[AgentPublic]

    model_config = ConfigDict(from_attributes=True)
