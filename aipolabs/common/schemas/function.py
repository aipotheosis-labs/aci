from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

import jsonschema
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aipolabs.common.enums import HttpLocation, HttpMethod, Protocol, Visibility
from aipolabs.common.validator import (
    validate_function_parameters_schema_common,
    validate_function_parameters_schema_rest_protocol,
)


class RestMetadata(BaseModel):
    method: HttpMethod
    path: str
    server_url: str


class GraphQLMetadata(BaseModel):
    """placeholder, not used yet"""

    pass


class FunctionCreate(BaseModel):
    name: str
    description: str
    tags: list[str]
    visibility: Visibility
    enabled: bool
    protocol: Protocol
    protocol_data: RestMetadata | GraphQLMetadata = Field(default_factory=dict)
    parameters: dict = Field(default_factory=dict)
    response: dict = Field(default_factory=dict)

    # validate parameters json schema
    @model_validator(mode="after")
    def validate_parameters(self) -> "FunctionCreate":

        # Validate that parameters schema itself is a valid JSON Schema
        jsonschema.validate(instance=self.parameters, schema=jsonschema.Draft7Validator.META_SCHEMA)

        # common validation
        validate_function_parameters_schema_common(self.parameters, f"{self.name}.parameters")

        # specific validation per protocol
        if self.protocol == Protocol.REST:
            validate_function_parameters_schema_rest_protocol(
                self.parameters,
                f"{self.name}.parameters",
                [location.value for location in HttpLocation],
            )
        else:
            pass

        return self

    # validate protocol_data against protocol type
    @model_validator(mode="after")
    def validate_metadata_by_protocol(self) -> "FunctionCreate":
        protocol_to_class = {Protocol.REST: RestMetadata}

        expected_class = protocol_to_class[self.protocol]
        if not isinstance(self.protocol_data, expected_class):
            raise ValueError(
                f"Protocol '{self.protocol}' requires protocol_data of type {expected_class.__name__}, "
                f"but got {type(self.protocol_data).__name__}"
            )
        return self


class FunctionsList(BaseModel):
    app_ids: list[UUID] | None = Field(
        default=None, description="List of app ids for filtering functions."
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of Functions per response."
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")


# TODO: add flag (e.g., verbose=true) to include detailed function info? (e.g., dev portal will need this)
class FunctionsSearch(BaseModel):
    app_ids: list[UUID] | None = Field(
        default=None, description="List of app ids for filtering functions."
    )
    intent: str | None = Field(
        default=None,
        description="Natural language intent for vector similarity sorting. Results will be sorted by relevance to the intent.",
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of Apps per response."
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")

    # empty intent or string with spaces should be treated as None
    @field_validator("intent")
    def validate_intent(cls, v: str | None) -> str | None:
        if v is not None and v.strip() == "":
            return None
        return v


class FunctionExecute(BaseModel):
    function_input: dict = Field(
        default_factory=dict, description="The input parameters for the function."
    )
    # TODO: can add other params like linked_account_owner_id


class FunctionBasic(BaseModel):
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class FunctionDetails(BaseModel):
    id: UUID
    app_id: UUID
    name: str
    description: str
    tags: list[str]
    visibility: Visibility
    enabled: bool
    protocol: Protocol
    protocol_data: dict
    parameters: dict
    response: dict

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InferenceProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class OpenAIFunctionDefinition(BaseModel):
    class OpenAIFunction(BaseModel):
        name: str
        strict: bool | None = None
        description: str
        parameters: dict

    type: Literal["function"] = "function"
    function: OpenAIFunction


class AnthropicFunctionDefinition(BaseModel):
    name: str
    description: str
    # equivalent to openai's parameters
    input_schema: dict


class FunctionExecutionResult(BaseModel):
    success: bool
    data: Any | None = None  # adding "| None" just for clarity
    error: str | None = None
