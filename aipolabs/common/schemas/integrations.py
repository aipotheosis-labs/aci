import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aipolabs.common.enums import SecurityScheme


class IntegrationPublic(BaseModel):
    id: UUID
    project_id: UUID
    app_id: UUID
    security_scheme: SecurityScheme
    security_config_overrides: dict
    enabled: bool
    all_functions_enabled: bool
    enabled_functions: list[UUID]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
