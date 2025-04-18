from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aci.common.enums import SecurityScheme


class AppConfigurationPublic(BaseModel):
    id: UUID
    project_id: UUID
    app_name: str
    security_scheme: SecurityScheme
    security_scheme_overrides: dict
    enabled: bool
    all_functions_enabled: bool
    enabled_functions: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppConfigurationCreate(BaseModel):
    """Create a new app configuration
    “all_functions_enabled=True” → ignore enabled_functions.
    “all_functions_enabled=False” AND non-empty enabled_functions → selectively enable that list.
    “all_functions_enabled=False” AND empty enabled_functions → all functions disabled.
    """

    app_name: str
    security_scheme: SecurityScheme
    # TODO: add typing/class to security_scheme_overrides
    security_scheme_overrides: dict = Field(default_factory=dict)
    all_functions_enabled: bool = Field(default=True)
    enabled_functions: list[str] = Field(default_factory=list)

    # validate:
    # when all_functions_enabled is True, enabled_functions provided by user should be empty
    @model_validator(mode="after")
    def check_all_functions_enabled(self) -> "AppConfigurationCreate":
        if self.all_functions_enabled and self.enabled_functions:
            raise ValueError(
                "all_functions_enabled and enabled_functions cannot be both True and non-empty"
            )
        return self


class AppConfigurationUpdate(BaseModel):
    security_scheme: SecurityScheme | None = None
    security_scheme_overrides: dict | None = None
    enabled: bool | None = None
    all_functions_enabled: bool | None = None
    enabled_functions: list[str] | None = None

    @model_validator(mode="after")
    def check_all_functions_enabled(self) -> "AppConfigurationUpdate":
        if self.all_functions_enabled and self.enabled_functions:
            raise ValueError(
                "all_functions_enabled and enabled_functions cannot be both True and non-empty"
            )
        return self


class AppConfigurationsList(BaseModel):
    app_names: list[str] | None = Field(default=None, description="Filter by app names.")
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results per response.",
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")
