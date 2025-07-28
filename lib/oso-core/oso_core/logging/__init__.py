import logging
import os
import sys
import typing as t

import colorlog

connected_to_application_logs = False

logger = logging.getLogger(__name__)


def add_oso_core_to_current_application_logging():
    """Originally created to ensure that oso_core logs appear in sqlmesh. This
    will automatically add the `oso_core` logger to the main running
    application."""
    import __main__

    global connected_to_application_logs

    try:
        app_name = os.path.basename(__main__.__file__)
    except AttributeError:
        # Do nothing if __main__.__file__ doesn't exist
        return
    if not connected_to_application_logs:
        extend_existing_logger("oso_core", app_name)
        connected_to_application_logs = True
        logger.info(f"oso_core logger connected to {app_name} application logs.")


def extend_existing_logger(target_logger_name: str, logger_name: str):
    """Extends an existing logger to aggregate logs for a different logger by
    adding a filter to the currently existing logger. This is useful for
    extending an already existing logger

    Args:
        target_logger_name (str): The name of the logger to extend.
        logger_name (str): The name of the logger to aggregate logs from.
    Returns:
        None
    """

    class MetricsToolsFilter(logging.Filter):
        def filter(self, record):
            return record.name == logger_name

    app_logger = logging.getLogger(target_logger_name)
    app_logger.addFilter(MetricsToolsFilter())


class ModuleFilter(logging.Filter):
    """Allows logs only from the specified module."""

    def __init__(self, module_name):
        super().__init__()
        self.module_name = module_name

    def filter(self, record):
        return record.name.startswith(self.module_name)


def setup_multiple_modules_logging(module_names: t.List[str]):
    for module_name in module_names:
        setup_module_logging(module_name)


# Configure logging
def setup_module_logging(
    module_name: str,
    level: int = logging.DEBUG,
    override_format: str = "",
    color: bool = False,
):
    logger = logging.getLogger(module_name)
    logger.setLevel(level)  # Adjust the level as needed

    # Create a handler that logs to stdout
    if color:
        format = "%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s - %(name)s - %(message)s"
        stdout_handler = colorlog.StreamHandler(sys.stdout)
        formatter = colorlog.ColoredFormatter(format, datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        format = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
        stdout_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(format, datefmt="%Y-%m-%dT%H:%M:%S")
    stdout_handler.setLevel(level)  # Adjust the level as needed

    # Add the filter to the handler
    stdout_handler.addFilter(ModuleFilter(module_name))

    # Set a formatter (optional)
    stdout_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(stdout_handler)
