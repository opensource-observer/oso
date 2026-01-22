import logging
import typing as t
from contextlib import asynccontextmanager, contextmanager
from unittest.mock import AsyncMock, Mock, create_autospec

from aiotrino.dbapi import ColumnDescription
from aiotrino.dbapi import Connection as AsyncConnection
from trino.dbapi import Connection


class FakeTrinoResource:
    # FIXME: We need to write a tool to check that all these methods are
    # compatible with the real TrinoResource interface. This was attempted with
    # the oso-core codegen tools but that is not fully sufficient. That tooling
    # is only good at making `typing.Protocol` and making class Fakes. That is
    # useful for instances where returned data is simple or uses
    # `pydantic.BaseModel`, but in cases where we need to Fake only some
    # portions of a class and have it be interface compatible. That's not easily
    # done with the current codegen tools. We need also some static analysis
    # tool.

    @classmethod
    def create(cls) -> "FakeTrinoResource":
        async_connection_mock = create_autospec(AsyncConnection, instance=True)
        sync_connection_mock = create_autospec(Connection, instance=True)
        async_cursor_mock = AsyncMock()
        sync_cursor_mock = Mock()
        async_cursor_mock.fetchone.side_effect = [[1], None]
        async_cursor_mock.get_description.return_value = [
            ColumnDescription(
                name="col1",
                type_code=1,
                display_size=2,
                internal_size=2,
                precision=0,
                scale=1,
                null_ok=False,
            ),
        ]
        async_cursor_mock.execute.return_value = async_cursor_mock

        async_connection_mock.cursor.return_value = async_cursor_mock
        sync_connection_mock.cursor.return_value = sync_cursor_mock

        return cls(
            async_connection_mock=async_connection_mock,
            sync_connection_mock=sync_connection_mock,
            async_cursor_mock=async_cursor_mock,
            sync_cursor_mock=sync_cursor_mock,
        )

    def __init__(
        self,
        async_connection_mock: t.Any,
        sync_connection_mock: t.Any,
        async_cursor_mock: t.Any,
        sync_cursor_mock: t.Any,
    ):
        self.async_connection_mock = async_connection_mock
        self.sync_connection_mock = sync_connection_mock
        self.async_cursor_mock = async_cursor_mock
        self.sync_cursor_mock = sync_cursor_mock

    @contextmanager
    def get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.Iterator[Connection]:
        yield self.sync_connection_mock

    @asynccontextmanager
    async def async_get_client(
        self,
        session_properties: t.Optional[t.Dict[str, t.Any]] = None,
        log_override: t.Optional[logging.Logger] = None,
        user: t.Optional[str] = None,
    ) -> t.AsyncIterator[AsyncConnection]:
        yield self.async_connection_mock
