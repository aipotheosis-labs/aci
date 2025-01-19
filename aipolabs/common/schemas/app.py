import re
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.schemas.function import FunctionBasic
from aipolabs.common.schemas.security_scheme import APIKeyScheme, OAuth2Scheme


class AppCreate(BaseModel):
    name: str
    display_name: str
    provider: str
    version: str
    description: str
    logo: str
    categories: list[str]
    visibility: Visibility
    active: bool
    security_schemes: dict[SecurityScheme, APIKeyScheme | OAuth2Scheme]

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[A-Z_]+$", v) or "__" in v:
            raise ValueError(
                "name must be uppercase, contain only letters and underscores, and not have consecutive underscores"
            )
        return v


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


class AppsList(BaseModel):
    """
    Parameters for listing Apps.
    TODO: add filters
    """

    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of Apps per response."
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")


class AppBasic(BaseModel):
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class AppBasicWithFunctions(AppBasic):
    functions: list[FunctionBasic]


class AppDetails(BaseModel):
    id: UUID
    name: str
    display_name: str
    provider: str
    version: str
    description: str
    logo: str | None
    categories: list[str]
    visibility: Visibility
    active: bool
    # Note this field is different from security_schemes in the db model. Here it's just a list of supported SecurityScheme.
    # the security_schemes field in the db model is a dict of supported security schemes and their config,
    # which contains sensitive information like OAuth2 client secret.
    supported_security_schemes: list[SecurityScheme] = Field(alias="security_schemes")
    functions: list[FunctionBasic]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("security_schemes", mode="before")
    @classmethod
    def extract_supported_security_schemes(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return [SecurityScheme(k) for k in v.keys()]
        return v
