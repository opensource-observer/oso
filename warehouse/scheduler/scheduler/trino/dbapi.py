from sqlglot import exp, parse_one
from trino.dbapi import Connection as BaseConnection
from trino.dbapi import Cursor as BaseCursor
from trino.dbapi import (
    DatabaseError,
    DataError,
    Error,
    IntegrityError,
    InterfaceError,
    InternalError,
    NotSupportedError,
    OperationalError,
    ProgrammingError,
    SegmentCursor,
    Warning,
    apilevel,
    paramstyle,
    threadsafety,
)
from trino.transaction import IsolationLevel

__all__ = [
    # https://www.python.org/dev/peps/pep-0249/#globals
    "apilevel",
    "threadsafety",
    "paramstyle",
    "connect",
    "Connection",
    "Cursor",
    # https://www.python.org/dev/peps/pep-0249/#exceptions
    "Warning",
    "Error",
    "InterfaceError",
    "DatabaseError",
    "DataError",
    "OperationalError",
    "IntegrityError",
    "InternalError",
    "ProgrammingError",
    "NotSupportedError",
]


def connect(*args, **kwargs):
    """Constructor for creating a connection to the database.

    See class :py:class:`Connection` for arguments.

    :returns: a :py:class:`Connection` object.
    """
    return Connection(*args, **kwargs)


class Connection(BaseConnection):
    def cursor(
        self, cursor_style: str = "row", legacy_primitive_types: bool | None = None
    ):
        """Return a new :py:class:`Cursor` object using the connection."""
        if self.isolation_level != IsolationLevel.AUTOCOMMIT:
            if self.transaction is None:
                self.start_transaction()
        if self.transaction is not None:
            request = self.transaction.request
        else:
            request = self._create_request()

        cursor_class = {
            # Add any custom Cursor classes here
            "segment": SegmentCursor,
            "row": Cursor,
        }.get(cursor_style.lower(), Cursor)

        return cursor_class(
            self,
            request,
            legacy_primitive_types=(
                legacy_primitive_types
                if legacy_primitive_types is not None
                else self.legacy_primitive_types
            ),
        )


class Cursor(BaseCursor):
    def executemany(self, operation, seq_of_params):
        try:
            expression = parse_one(operation, dialect="trino")
        except Exception:
            expression = None

        if expression and isinstance(expression, exp.Insert):
            values = expression.find(exp.Values)
            if values:
                new_values = []
                for row in seq_of_params:
                    new_values.append(
                        exp.Tuple(expressions=[exp.convert(v) for v in row])
                    )
                if new_values:
                    values.set("expressions", new_values)
                    return self.execute(expression.sql(dialect="trino"))
        return super().executemany(operation, seq_of_params)
