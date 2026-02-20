import sys
from decimal import Decimal

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
    # Trino's query.max-length defaults to 1,000,000 characters.
    # We use 900KB as the limit to leave headroom for the INSERT template.
    _MAX_QUERY_BYTES = 900_000

    def executemany(self, operation, seq_of_params):
        try:
            expression = parse_one(operation, dialect="trino")
        except Exception:
            expression = None

        if expression and isinstance(expression, exp.Insert):
            values = expression.expression
            if isinstance(values, exp.Values):
                # Render each row's SQL once upfront
                tuple_sqls = [
                    exp.Tuple(
                        expressions=[
                            exp.Cast(
                                this=exp.Literal.string(str(v)),
                                to=exp.DataType.build("DECIMAL"),
                            )
                            if isinstance(v, Decimal) and abs(v) > sys.maxsize
                            else exp.convert(v)
                            for v in row
                        ]
                    ).sql(dialect="trino")
                    for row in seq_of_params
                ]

                if not tuple_sqls:
                    return super().executemany(operation, seq_of_params)

                # Build the INSERT prefix: everything before the values list
                # e.g. "INSERT INTO schema.table (...) VALUES "
                values.set(
                    "expressions",
                    [exp.Tuple(expressions=[exp.convert(None)])],
                )
                placeholder_sql = expression.sql(dialect="trino")
                prefix = placeholder_sql.split("VALUES", 1)[0] + "VALUES "
                prefix_bytes = len(prefix.encode("utf-8"))

                # Chunk rows so each INSERT stays under the byte limit
                chunk: list[str] = []
                chunk_size = prefix_bytes

                for tsql in tuple_sqls:
                    entry_bytes = len(tsql.encode("utf-8")) + 2  # +2 for ", "
                    if chunk and chunk_size + entry_bytes > self._MAX_QUERY_BYTES:
                        self.execute(prefix + ", ".join(chunk))
                        chunk = []
                        chunk_size = prefix_bytes
                    chunk.append(tsql)
                    chunk_size += entry_bytes

                # tuple_sqls is non-empty so chunk always has at least one entry
                return self.execute(prefix + ", ".join(chunk))
        return super().executemany(operation, seq_of_params)
