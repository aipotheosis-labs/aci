import logging
from typing import Any

from pydantic import BaseModel, ValidationError

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


class LogFieldSchemas:
    """Centralized schema definitions for log field validation."""

    # Default python logging attributes will be ignored and not validated
    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    DEFAULT_FIELDS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
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
        "thread",
        "threadName",
    }

    # Normal log fields
    NORMAL_FIELDS = {
        "url",
        "url_scheme",
        "http_version",
        "http_method",
        "http_path",
        "query_params",
        "request_body",
        "status_code",
        "content_length",
        "duration",
        "client_ip",
        "user_agent",
        "x_forwarded_proto",
        "request_id",
        "agent_id",
        "org_id",
        "api_key_id",
        "project_id",
        "user_id",
    }

    # Telemetry field schemas with their corresponding Pydantic models
    TELEMETRY_FIELDS = {
        "function_execution": FunctionExecutionSchema,
        "search_functions": SearchFunctionsSchema,
        "search_apps": SearchAppsSchema,
        "get_function_definition": GetFunctionDefinitionSchema,
    }


class PydanticFieldValidator:
    """Handles Pydantic-based validation for different field types."""

    def __init__(self) -> None:
        self.schemas: LogFieldSchemas = LogFieldSchemas()
        # Create single instances for context and HTTP validation
        self.normal_log_fields_validator: type[NormalLogFieldsSchema] = NormalLogFieldsSchema

    def validate_normal_field(self, field_name: str, value: Any) -> bool:
        """Validate a single normal field."""
        try:
            # Create a partial model with just this field
            field_data = {field_name: value}
            self.normal_log_fields_validator(**field_data)
            return True
        except ValidationError as e:
            logger.exception(f"Normal field '{field_name}' validation failed: {e}")
            return False

    def validate_telemetry_field(self, field_name: str, value: Any) -> bool:
        """Validate a telemetry schema using its Pydantic model."""
        try:
            schema_class = self.schemas.TELEMETRY_FIELDS[field_name]
            schema_class(**value)
            return True
        except ValidationError as e:
            logger.exception(f"Telemetry field '{field_name}' validation failed: {e}")
            return False
        except TypeError as e:
            logger.exception(f"Telemetry field '{field_name}' type error: {e}")
            return False


class LogSchemaFilter(logging.Filter):
    """
    Custom logging filter that validates and organizes log fields using Pydantic.

    Moves non-standard fields into an 'extra_attributes' field while validating
    known fields against their Pydantic schemas.
    """

    def __init__(self) -> None:
        super().__init__()
        self.schemas: LogFieldSchemas = LogFieldSchemas()
        self.validator: PydanticFieldValidator = PydanticFieldValidator()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and organize log record fields with Pydantic validation."""
        extra_attributes = {}

        # Process all fields in the record
        for key, value in list(record.__dict__.items()):
            if key == "extra_attributes":
                continue

            field_type = self._get_field_type(key)
            if field_type == "default":
                continue
            elif field_type == "extra_attributes":
                extra_attributes[key] = value
                delattr(record, key)
            elif not self._validate_field(key, value, field_type):
                # Field failed validation, but we keep it in the record
                # The validation error was already logged
                pass

        # Add extra attributes if any exist
        if extra_attributes:
            record.extra_attributes = extra_attributes

        return True

    def _get_field_type(self, field_name: str) -> str:
        """Determine the type category of a field."""
        if field_name in self.schemas.DEFAULT_FIELDS:
            return "default"
        elif field_name in self.schemas.NORMAL_FIELDS:
            return "normal"
        elif field_name in self.schemas.TELEMETRY_FIELDS:
            return "telemetry"
        else:
            return "extra_attributes"

    def _validate_field(self, field_name: str, value: Any, field_type: str) -> bool:
        """Validate a field based on its type category using Pydantic."""
        try:
            if field_type == "normal":
                return self.validator.validate_normal_field(field_name, value)
            elif field_type == "telemetry":
                return self.validator.validate_telemetry_field(field_name, value)

            return True

        except Exception as e:
            logger.exception(f"Unexpected validation error for field '{field_name}': {e}")
            return False
