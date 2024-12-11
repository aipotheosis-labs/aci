import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.schemas.function import FunctionPublic


class AppCreate(BaseModel):
    name: str
    display_name: str
    provider: str
    version: str
    description: str
    logo: str
    categories: list[str]
    visibility: Visibility
    enabled: bool
    # TODO: consider making schema for each security scheme instead of using dict
    security_schemes: dict[SecurityScheme, dict] = Field(default_factory=dict)

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[A-Z_]+$", v) or "__" in v:
            raise ValueError(
                "name must be uppercase, contain only letters and underscores, and not have consecutive underscores"
            )
        return v


class AppPublic(BaseModel):
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class AppDetails(AppPublic):
    functions: list[FunctionPublic]
