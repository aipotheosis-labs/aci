import logging

logger = logging.getLogger(__name__)

_DEFAULT_LOG_FIELDS = [
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

_ALLOWED_CUSTOM_LOG_FIELDS = [
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
    "function_execution",
    "search_functions",
    "search_apps",
    "get_function_definition",
]


class LogSchemaFilter(logging.Filter):
    """
    Moves non-standard fields into an 'extra_attributes'
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and organize log record fields with Pydantic validation."""

        extra_attributes = {}
        # Process all fields in the record
        for field, value in list(record.__dict__.items()):
            # we reserve the field name "extra_attributes" for the extra_attributes dict
            # so any value with this field name will be ignored
            if field == "extra_attributes":
                continue
            elif field in _DEFAULT_LOG_FIELDS or field in _ALLOWED_CUSTOM_LOG_FIELDS:
                continue
            else:
                # store not allowed fields in extra_attributes
                extra_attributes[field] = value
                delattr(record, field)

        if extra_attributes:
            record.__dict__["extra_attributes"] = extra_attributes

        return True
