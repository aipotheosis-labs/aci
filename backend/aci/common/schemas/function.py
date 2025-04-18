from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

import jsonschema
from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator

from aci.common.db.sql_models import MAX_STRING_LENGTH
from aci.common.enums import (
    FunctionDefinitionFormat,
    HttpLocation,
    HttpMethod,
    Protocol,
    Visibility,
)
from aci.common.validator import (
    validate_function_parameters_schema_common,
    validate_function_parameters_schema_rest_protocol,
)


class RestMetadata(BaseModel):
    method: HttpMethod
    path: str
    server_url: str


class ConnectorMetadata(RootModel[dict]):
    """placeholder, allow any metadata for connector for now"""


class FunctionUpsert(BaseModel):
    name: str
    description: str
    tags: list[str]
    visibility: Visibility
    active: bool
    protocol: Protocol
    # TODO: should get rid of default dict?
    # TODO: we need to use left_to_right union mode to avoid pydantic validating RestMetadata
    # input against ConnectorMetadata schema (which allows any dict)
    protocol_data: Annotated[
        RestMetadata | ConnectorMetadata, Field(default_factory=dict, union_mode="left_to_right")
    ]
    parameters: dict = Field(default_factory=dict)
    response: dict = Field(default_factory=dict)

    # validate parameters json schema
    @model_validator(mode="after")
    def validate_parameters(self) -> "FunctionUpsert":
        # Validate that parameters schema itself is a valid JSON Schema
        jsonschema.validate(instance=self.parameters, schema=jsonschema.Draft7Validator.META_SCHEMA)

        # common validation
        validate_function_parameters_schema_common(self.parameters, f"{self.name}.parameters")

        # specific validation per protocol
        if self.protocol == Protocol.REST:
            validate_function_parameters_schema_rest_protocol(
                self.parameters,
                f"{self.name}.parameters",
                [str(location) for location in HttpLocation],
            )
        else:
            pass

        return self

    # validate protocol_data against protocol type
    @model_validator(mode="after")
    def validate_metadata_by_protocol(self) -> "FunctionUpsert":
        protocol_to_class = {
            Protocol.REST: RestMetadata,
            Protocol.CONNECTOR: ConnectorMetadata,
        }

        expected_class = protocol_to_class[self.protocol]
        if not isinstance(self.protocol_data, expected_class):
            raise ValueError(
                f"Protocol '{self.protocol}' requires protocol_data of type {expected_class.__name__}, "
                f"but got {type(self.protocol_data).__name__}"
            )
        return self


class FunctionEmbeddingFields(BaseModel):
    """
    Fields used to generate function embedding.
    """

    # TODO: more relevant fields?
    name: str
    description: str
    parameters: dict


class FunctionsList(BaseModel):
    app_names: list[str] | None = Field(
        default=None, description="List of app names for filtering functions."
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of Functions per response.",
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")


class FunctionsSearch(BaseModel):
    app_names: list[str] | None = Field(
        default=None,
        description="List of app names for filtering functions.",
    )
    intent: str | None = Field(
        default=None,
        description="Natural language intent for vector similarity sorting. Results will be sorted by relevance to the intent.",
    )
    allowed_apps_only: bool = Field(
        default=False,
        description="If true, only returns functions of apps that are allowed by the agent/accessor, identified by the api key.",
    )
    format: FunctionDefinitionFormat = Field(
        default=FunctionDefinitionFormat.BASIC,
        description="The format of the function definition to return. e.g., 'openai', 'anthropic' or 'basic' which only returns name and description.",
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of Functions per response."
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset.")

    # empty intent or string with spaces should be treated as None
    @field_validator("intent")
    def validate_intent(cls, v: str | None) -> str | None:
        if v is not None and v.strip() == "":
            return None
        return v

    @field_validator("app_names")
    def validate_app_names(cls, v: list[str] | None) -> list[str] | None:
        # remove empty strings
        if v is not None:
            v = [app_name for app_name in v if app_name.strip()]
        return v


class FunctionExecute(BaseModel):
    function_input: dict = Field(
        default_factory=dict, description="The input parameters for the function."
    )
    linked_account_owner_id: str = Field(
        ...,
        max_length=MAX_STRING_LENGTH,
        description="The owner id of the linked account. This is the id of the linked account owner in the linked account provider.",
    )


class FunctionDetails(BaseModel):
    id: UUID
    app_name: str
    name: str
    description: str
    tags: list[str]
    visibility: Visibility
    active: bool
    protocol: Protocol
    protocol_data: dict
    parameters: dict
    response: dict

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpenAIFunction(BaseModel):
    name: str
    strict: bool | None = None
    description: str
    parameters: dict


class OpenAIFunctionDefinition(BaseModel):
    type: Literal["function"] = "function"
    function: OpenAIFunction


class OpenAIResponsesFunctionDefinition(BaseModel):
    type: Literal["function"] = "function"
    name: str
    description: str
    parameters: dict


class AnthropicFunctionDefinition(BaseModel):
    name: str
    description: str
    # equivalent to openai's parameters
    input_schema: dict


class BasicFunctionDefinition(BaseModel):
    """
    Our own custom function definition, only returns name and description.
    useful for the "search" endpoint, to reduce the amount of data returned.
    """

    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class FunctionExecutionResult(BaseModel):
    success: bool
    data: Any | None = None  # adding "| None" just for clarity
    error: str | None = None
