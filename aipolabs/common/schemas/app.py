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


class AppsSearch(BaseModel):
    """
    Parameters for searching applications.
    TODO: category enum?
    TODO: filter by similarity score?
    """

    intent: str | None = Field(
        default=None,
        description="Natural language intent for vector similarity sorting. Results will be sorted by relevance to the intent.",
    )
    categories: list[str] | None = Field(
        default=None, description="List of categories for filtering."
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of Apps per response."
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")

    # need this in case user set {"categories": None} which will translate to [''] in the params
    @field_validator("categories")
    def validate_categories(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            # Remove any empty strings from the list
            v = [category for category in v if category.strip()]
            # If after removing empty strings the list is empty, set it to None
            if not v:
                return None
        return v

    # empty intent or string with spaces should be treated as None
    @field_validator("intent")
    def validate_intent(cls, v: str | None) -> str | None:
        if v is not None and v.strip() == "":
            return None
        return v
