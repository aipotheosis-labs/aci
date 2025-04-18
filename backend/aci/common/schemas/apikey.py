from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aci.common.enums import APIKeyStatus


class APIKeyPublic(BaseModel):
    id: UUID
    key: str
    agent_id: UUID
    status: APIKeyStatus

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
