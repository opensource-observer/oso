import logging


def setup_logging(verbosity: int):
    """Configure logging level based on verbosity."""
    match verbosity:
        case 0:
            return logging.getLogger("oso-agent").setLevel(logging.WARNING)
        case 1:
            return logging.getLogger("oso-agent").setLevel(logging.INFO)
        case _:
            return logging.getLogger("oso-agent").setLevel(logging.DEBUG)
