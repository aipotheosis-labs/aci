import logging
import shutil
from logging.handlers import RotatingFileHandler

import logfire


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


def create_headline(title: str, fill_char: str = "-") -> str:
    """Create a header that fills the terminal width with the given title centered.

    Args:
        title: The text to center in the header
        fill_char: The character to use for filling (default: "-")

    Returns:
        A string containing the formatted header with green title text
    """
    # ANSI escape codes for green text and reset
    GREEN = "\033[32m"
    RESET = "\033[0m"

    terminal_width = shutil.get_terminal_size().columns or 80
    padded_title = f" {GREEN}{title}{RESET} "  # Add green color to title
    padding = fill_char * ((terminal_width - len(title) - 2) // 2)  # -2 for the spaces
    header = f"{padding}{padded_title}{padding}"

    # Add extra fill_char if the total length is off by one due to integer division
    if len(header) - len(GREEN) - len(RESET) < terminal_width:
        header += fill_char

    return header
