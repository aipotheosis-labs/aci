import logging
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Pydantic models for different schema types
class FunctionExecutionSchema(BaseModel):
    """Schema for function execution log data."""

    app_name: str | None = None
    function_name: str | None = None
    linked_account_owner_id: str | None = None
    function_execution_duration: float | None = None
    function_input: str | None = None
    function_execution_result_success: bool | None = None
    function_execution_result_error: str | None = None
    function_execution_result_data: str | None = None
    function_execution_result_data_size: int | None = None


class SearchFunctionsSchema(BaseModel):
    """Schema for search functions log data."""

    query_params_json: str | None = None
    function_names: list[str] | None = None


class SearchAppsSchema(BaseModel):
    """Schema for search apps log data."""

    query_params_json: str | None = None
    apps_names: list[str] | None = None


class GetFunctionDefinitionSchema(BaseModel):
    """Schema for get function definition log data."""

    format: str | None = None
    function_name: str | None = None


class NormalLogFieldsSchema(BaseModel):
    """Schema for HTTP-related fields."""

    url: str | None = None
    url_scheme: str | None = None
    http_version: str | None = None
    http_method: str | None = None
    http_path: str | None = None
    query_params: dict | None = None
    request_body: str | None = None
    status_code: int | None = None
    content_length: str | None = None
    duration: float | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    x_forwarded_proto: str | None = None
    request_id: str | None = None
    agent_id: str | None = None
    org_id: str | None = None
    api_key_id: str | None = None
    project_id: str | None = None
    user_id: str | None = None


class TelemetryFieldsSchema(BaseModel):
    """Schema for telemetry fields."""

    function_execution: FunctionExecutionSchema
    search_functions: SearchFunctionsSchema
    search_apps: SearchAppsSchema
    get_function_definition: GetFunctionDefinitionSchema


_DEFAULT_FIELDS = [
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "file",
    "filename",
    "funcName",
    "level",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msg",
    "msecs",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "timestamp",
    "thread",
    "threadName",
]

_NORMAL_FIELDS = list(NormalLogFieldsSchema.model_fields.keys())

_TELEMETRY_FIELDS = list(TelemetryFieldsSchema.model_fields.keys())


class FieldType(StrEnum):
    """Enumeration for log field types."""

    DEFAULT = "default"  # https://docs.python.org/3/library/logging.html#logrecord-attributes logging attribute with format rename
    NORMAL = "normal"  # fields that are not telemetry(http and request context)
    TELEMETRY = "telemetry"  # fields that are telemetry(search_apps, search_functions, get_function_definition, function_execution)
    EXTRA_ATTRIBUTES = "extra_attributes"  # all other fields


class PydanticFieldValidator:
    """Handles Pydantic-based validation for different field types."""

    @staticmethod
    def get_field_type(field_name: str) -> FieldType:
        """Determine the type category of a field."""
        if field_name in _DEFAULT_FIELDS:
            return FieldType.DEFAULT
        elif field_name in _NORMAL_FIELDS:
            return FieldType.NORMAL
        elif field_name in _TELEMETRY_FIELDS:
            return FieldType.TELEMETRY
        else:
            return FieldType.EXTRA_ATTRIBUTES

    @staticmethod
    def validate_field(field_name: str, value: Any, field_type: FieldType) -> None:
        """Validate a field based on its type category using Pydantic."""
        try:
            if field_type is FieldType.NORMAL:
                NormalLogFieldsSchema.model_validate({field_name: value})

            elif field_type is FieldType.TELEMETRY:
                telemetry_field = TelemetryFieldsSchema.model_fields.get(field_name)
                if telemetry_field is not None and telemetry_field.annotation is not None:
                    # Validate the value directly against the field's schema type
                    telemetry_field.annotation.model_validate({field_name: value})
                else:
                    raise ValueError(f"Telemetry field '{field_name}' not found in schema")
        except Exception:
            raise


class LogSchemaFilter(logging.Filter):
    """
    Custom logging filter that validates and organizes log fields using Pydantic.

    Moves non-standard fields into an 'extra_attributes' field while validating
    known fields against their Pydantic schemas.
    """

    def __init__(self) -> None:
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and organize log record fields with Pydantic validation."""
        try:
            extra_attributes = {}
            # Process all fields in the record
            for field, value in list(record.__dict__.items()):
                if field == FieldType.EXTRA_ATTRIBUTES:
                    continue

                expected_type = PydanticFieldValidator.get_field_type(field)

                if expected_type is FieldType.DEFAULT:
                    continue
                elif expected_type in (FieldType.NORMAL, FieldType.TELEMETRY):
                    try:
                        PydanticFieldValidator.validate_field(field, value, expected_type)
                    except Exception:
                        raise
                elif expected_type is FieldType.EXTRA_ATTRIBUTES:
                    extra_attributes[field] = value
                    delattr(record, field)

            # Add all fields that are not normal or telemetry to extra_attributes
            if extra_attributes:
                record.extra_attributes = extra_attributes

        except Exception:
            logger.exception("Unexpected error in LogSchemaFilter.filter")
            return False

        return True
