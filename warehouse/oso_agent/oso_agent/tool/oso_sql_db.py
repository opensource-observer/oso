# pyright: reportCallIssue=false
import asyncio
import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from llama_index.core.utilities.sql_wrapper import SQLDatabase
from sqlalchemy import MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.engine.interfaces import ReflectedColumn

from .oso_mcp_client import OsoMcpClient

logger = logging.getLogger(__name__)


class OsoSqlDatabase(SQLDatabase):
    """OSO SQL Database.

    This subclass overrides the SQLDatabase class in order to fit into
    LlamaIndex abstractions

    Args:
        oso_mcp_url (str): URL of the OSO MCP server.
        ignore_tables (Optional[List[str]]): List of table names to ignore. If set,
            include_tables must be None.
        include_tables (Optional[List[str]]): List of table names to include. If set,
            ignore_tables must be None.
        sample_rows_in_table_info (int): The number of sample rows to include in table
            info.
        custom_table_info (Optional[dict]): Custom table info to use.
        max_string_length (int): The maximum string length to use.

    """
    

    def __init__(
        self,
        oso_client: OsoMcpClient,
        tables: Set[str],
        sample_rows_in_table_info: int,
        max_string_length: int,
    ):
        #super().__init__(engine=create_engine("")) 
        self._oso_client = oso_client
        self._tables = tables
        self._sample_rows_in_table_info = sample_rows_in_table_info
        self._max_string_length = max_string_length

    @classmethod
    async def create(
        cls,
        oso_mcp_url: str,
        ignore_tables: Optional[List[str]] = None,
        include_tables: Optional[List[str]] = None,
        sample_rows_in_table_info: int = 3,
        max_string_length: int = 300,
    ):
        """Create engine from database URI."""
        oso_client = OsoMcpClient(oso_mcp_url)

        all_tables = await oso_client.list_tables()
        all_tables_set = set(all_tables)
        usable_tables = sorted(all_tables)
        if include_tables and ignore_tables:
            raise ValueError("Cannot specify both include_tables and ignore_tables")
        elif include_tables:
            include_tables_set = set(include_tables)
            missing_tables = include_tables_set - all_tables_set
            if missing_tables:
                raise ValueError(
                    f"include_tables {missing_tables} not found in database"
                )
            usable_tables = sorted(include_tables_set)
        elif ignore_tables:
            ignore_tables_set = set(ignore_tables)
            missing_tables = ignore_tables_set - all_tables_set
            if missing_tables:
                raise ValueError(
                    f"ignore_tables {missing_tables} not found in database"
                )
            usable_tables = sorted(all_tables_set - ignore_tables_set)
        usable_tables_set = set(usable_tables)

        if not isinstance(sample_rows_in_table_info, int):
            raise TypeError("sample_rows_in_table_info must be an integer")
        
        result = cls(oso_client, usable_tables_set, sample_rows_in_table_info, max_string_length)
        return result

    @property
    def engine(self) -> Engine:
        """Return SQL Alchemy engine."""
        raise NotImplementedError("OsoSqlDatabase does not support SqlAlchemy.")

    @property
    def metadata_obj(self) -> MetaData:
        """Return SQL Alchemy metadata."""
        raise NotImplementedError("OsoSqlDatabase does not support SqlAlchemy.")

    @property
    def dialect(self) -> str:
        """Return string representation of dialect to use."""
        return "trino"

    def get_usable_table_names(self) -> Iterable[str]:
        """Get names of tables available."""
        return sorted(self._tables)

    def get_table_columns(self, table_name: str) -> List[ReflectedColumn]:
        """Get table columns."""
        logger.debug("Getting table columns for table: %s", table_name)
        loop = asyncio.get_event_loop()
        coroutine = self._oso_client.get_table_schema(table_name)
        table_schema = loop.run_until_complete(coroutine)
        columns = [ReflectedColumn(name=col.name, type=col.type, comment=col.description) for col in table_schema]
        return columns

    def get_single_table_info(self, table_name: str) -> str:
        """Get table info for a single table."""
        logger.debug("Getting table info for table: %s", table_name)
        loop = asyncio.get_event_loop()
        coroutine = self._oso_client.get_table_schema(table_name)
        table_schema = loop.run_until_complete(coroutine)

        columns = []
        for column in table_schema:
            if column.description:
                columns.append(f"{column.name} ({column.type!s}): '{column.description}'")
            else:
                columns.append(f"{column.name} ({column.type!s})")
        column_str = ", ".join(columns)
        info = f"Table '{table_name}' has columns: {column_str}, "
        return info

    def insert_into_table(self, table_name: str, data: dict) -> None:
        """Insert data into a table.
        This method is not implemented for OsoSqlDatabase, as it is read-only.
        """
        raise NotImplementedError("OsoSqlDatabase does not support inserting data.")

    def truncate_word(self, content: Any, *, length: int, suffix: str = "...") -> str:
        """
        Truncate a string to a certain number of words, based on the max string
        length.
        """
        if not isinstance(content, str) or length <= 0:
            return content

        if len(content) <= length:
            return content

        return content[: length - len(suffix)].rsplit(" ", 1)[0] + suffix
    

    def run_sql(self, command: str) -> Tuple[str, Dict]:
        """Execute a SQL statement and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.
        """
        logger.debug("Running SQL command: %s", command)

        line_split = [ line.lower() for line in command.strip().split('\n')]
        if self.dialect.lower() in line_split:
            if line_split[0] == self.dialect.lower():
                command = "\n".join(line_split[1:])

        query_results = asyncio.run(self._oso_client.query_oso(command))
        truncated_results = []
        col_keys = []
        for row in query_results:
            # truncate each column, then convert the row to a tuple
            truncated_row = tuple(
                self.truncate_word(val, length=self._max_string_length)
                for val in row.values()
            )
            col_keys = [column for column in row.keys()]
            truncated_results.append(truncated_row)
        return str(truncated_results), {
            "result": truncated_results,
            "col_keys": col_keys,
        }