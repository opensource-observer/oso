class DialectError(Exception):
    """Base class for query rewriter dialect errors."""

    pass


class ConfigError(Exception):
    """Configuration related errors."""

    pass


class TableResolutionError(Exception):
    """Errors related to table resolution."""

    def __init__(self, unresolved_tables: list[str]):
        self.unresolved_tables = unresolved_tables
        message = (
            f"Tables do not exist or are inaccessible: {', '.join(unresolved_tables)}"
        )
        super().__init__(message)
