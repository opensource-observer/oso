import logging

import structlog

STRUCTURED_LOGGING_CONFIGURED = False


def flatten_extras(
    logger: logging.Logger, log_method: str, event_dict: structlog.types.EventDict
):
    """This flattens the extras dict so that it can be used in the log message."""
    if "extra" in event_dict:
        for key, value in event_dict["extra"].items():
            event_dict[key] = value
        del event_dict["extra"]
    return event_dict


def event_type(
    logger: logging.Logger, log_method: str, event_dict: structlog.types.EventDict
):
    """This allows us to add an event_type to logs so we can do filtering in the
    log UI"""

    if "event_type" not in event_dict:
        event_dict["event_type"] = "default"

    return event_dict


def configure_structured_logging() -> None:
    """Configure structured logging for the application. This was taken almost
    directly from the structlog docs. See:

    https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging

    This sets up a structured handler at the root logger. It does not configure
    the level of the root logger, so it is up to the user to enable the
    appropriate level so that logs appear on stdout.

    This should be called at the start of an application.
    """
    global STRUCTURED_LOGGING_CONFIGURED
    if STRUCTURED_LOGGING_CONFIGURED:
        return
    STRUCTURED_LOGGING_CONFIGURED = True

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors = [
        flatten_extras,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        event_type,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
