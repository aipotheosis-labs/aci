import datetime
import logging
from logging.handlers import RotatingFileHandler
from typing import Any

import logfire
from opensearchpy import OpenSearch

LOCAL_OPENSEARCH_LOG_INDEX_PREFIX = "aci-logs-local-"


# the setup is called once at the start of the app
def setup_logging(
    formatter: logging.Formatter | None = None,
    level: int = logging.INFO,
    filters: list[logging.Filter] | None = None,
    include_file_handler: bool = False,
    file_path: str | None = None,
    environment: str = "local",
) -> None:
    if filters is None:
        filters = []

    # Add OpenSearch filter for local environment to avoid duplicate logs
    if environment == "local":
        filters.append(LocalOpenSearchFilter())

    if formatter is None:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)  # Set the root logger level

    # Create a console handler (for output to console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    for filter in filters:
        console_handler.addFilter(filter)

    root_logger.addHandler(console_handler)

    if include_file_handler:
        if file_path is None:
            raise ValueError("file_path must be provided if include_file_handler is True")
        file_handler = RotatingFileHandler(file_path, maxBytes=10485760, backupCount=10)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        for filter in filters:
            file_handler.addFilter(filter)
        root_logger.addHandler(file_handler)

    if environment != "local":
        root_logger.addHandler(logfire.LogfireLoggingHandler())
    else:
        # Add OpenSearch handler for local environment to send logs to OpenSearch
        opensearch_handler = LocalOpenSearchHandler()
        for filter in filters:
            opensearch_handler.addFilter(filter)
        root_logger.addHandler(opensearch_handler)

    # Set up module-specific loggers if necessary (e.g., with different levels)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


class LocalOpenSearchFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Filter out logs that contain OpenSearch-related messages
        return not (
            "opensearch" in record.name.lower()
            or "opensearch" in record.getMessage().lower()
            or "POST http://opensearch" in record.getMessage()
        )


class LocalOpenSearchHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        # Because opensearch client will also output logs, we need to filter them out
        # We need create client here to avoid circular import
        self.opensearch_client: OpenSearch = OpenSearch(
            hosts=[{"host": "opensearch", "port": 9200}],
            http_auth=("admin", "admin"),
            use_ssl=False,
            verify_certs=False,
        )

    def emit(self, record: logging.LogRecord) -> None:
        # get timestamp from record's timestamp field
        timestamp = record.created
        timestamp_iso = datetime.datetime.fromtimestamp(timestamp).isoformat()

        log_body: dict[
            str, str | int | float | bool | list[Any] | dict[str, Any] | tuple[Any, ...] | None
        ] = {
            "message": record.getMessage(),
            "level": record.levelname,
            "@timestamp": timestamp_iso,
        }

        # Filter out non-serializable objects
        for key, value in record.__dict__.items():
            if isinstance(value, str | int | float | bool | list | dict | tuple | type(None)):
                log_body[key] = value
            else:
                log_body[key] = str(value)  # Convert any non-serializable objects to string

        # Create daily index name in format: aci-logs-YYYY.MM.DD
        index_name = f"{LOCAL_OPENSEARCH_LOG_INDEX_PREFIX}{datetime.datetime.fromtimestamp(timestamp).strftime('%Y.%m.%d')}"

        self.opensearch_client.index(
            index=index_name,
            body=log_body,
        )
