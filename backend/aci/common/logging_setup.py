import logging
from logging.handlers import RotatingFileHandler

import logfire

from aci.server.context import (
    agent_id_ctx_var,
    api_key_id_ctx_var,
    org_id_ctx_var,
    project_id_ctx_var,
    request_id_ctx_var,
)


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

    # Set up module-specific loggers if necessary (e.g., with different levels)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Only add attributes when values are not None
        request_id = request_id_ctx_var.get()
        if request_id is not None:
            record.__dict__["request_id"] = request_id

        api_key_id = api_key_id_ctx_var.get()
        if api_key_id is not None:
            record.__dict__["api_key_id"] = api_key_id

        project_id = project_id_ctx_var.get()
        if project_id is not None:
            record.__dict__["project_id"] = project_id

        agent_id = agent_id_ctx_var.get()
        if agent_id is not None:
            record.__dict__["agent_id"] = agent_id

        org_id = org_id_ctx_var.get()
        if org_id is not None:
            record.__dict__["org_id"] = org_id

        return True
