from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aipolabs.common.enums import SecurityScheme

if TYPE_CHECKING:
    from typing import Type


class IntegrationPublic(BaseModel):
    id: UUID
    project_id: UUID
    app_id: UUID
    security_scheme: SecurityScheme
    security_config_overrides: dict
    enabled: bool
    all_functions_enabled: bool
    enabled_functions: list[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntegrationCreate(BaseModel):
    app_name: str
    security_scheme: SecurityScheme
    # TODO: add typing/class to security_config_overrides
    security_config_overrides: dict = Field(default_factory=dict)
    # TODO: add all_functions_enabled/enabled_functions fields


class IntegrationUpdate(BaseModel):
    security_scheme: SecurityScheme | None = None
    security_config_overrides: dict | None = None
    enabled: bool | None = None
    all_functions_enabled: bool | None = None
    enabled_functions: list[UUID] | None = None

    @model_validator(mode="after")
    def check_enabled_functions(
        cls: "Type[IntegrationUpdate]", instance: "IntegrationUpdate"
    ) -> "IntegrationUpdate":
        # if enabled_functions is provided and length is not 0,
        # all_functions_enabled must be False (or not provided), and if provided, we set it to False
        if instance.enabled_functions and len(instance.enabled_functions) != 0:
            if instance.all_functions_enabled:
                # TODO: double confirm ValueError maps to 422
                raise ValueError(
                    "When 'enabled_functions' is provided and not empty, "
                    "'all_functions_enabled' must be False"
                )
            instance.all_functions_enabled = False
        return instance
