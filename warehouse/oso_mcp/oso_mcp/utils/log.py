import logging
import sys


class ModuleFilter(logging.Filter):
    """Allows logs only from the specified module."""

    def __init__(self, module_name):
        super().__init__()
        self.module_name = module_name

    def filter(self, record):
        return record.name.startswith(self.module_name)


def setup_logging(verbosity: int):
    """Configure logging level based on verbosity."""
    match verbosity:
        case 0:
            level = logging.WARNING
        case 1:
            level = logging.INFO
        case _:
            level = logging.DEBUG

    logger = logging.getLogger("oso-mcp")
    logger.setLevel(level)

    # Create a handler that logs to stdout
    format = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(format, datefmt="%Y-%m-%dT%H:%M:%S")
    stdout_handler.setLevel(level)

    # Add the filter to the handler
    stdout_handler.addFilter(ModuleFilter("oso-mcp"))

    # Set a formatter (optional)
    stdout_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(stdout_handler)

    logger.info("MCP Logging initialized")
