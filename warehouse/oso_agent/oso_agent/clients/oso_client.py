from dataclasses import dataclass
from typing import Any, List, cast

from pandas import DataFrame
from pyoso import Client

from ..util.errors import AgentRuntimeError


@dataclass
class ColumnSchema:
    name: str
    type: str
    description: str = ""


class OsoClient:
    """A client for interacting with the OSO server."""

    def __init__(self, api_key: str):
        self.client = Client(
            api_key=api_key,
        )

    async def _query_client(self, query: str) -> DataFrame:
        try:
            return self.client.to_pandas(query)
        except Exception as e:
            raise AgentRuntimeError(f"Error calling pyoso: {str(e)}")

    async def query_oso(self, query: str) -> list[dict[str, Any]]:
        """Query the pyoso server with a SQL query."""

        # Remove any trailing semicolon from the query
        if query.strip().endswith(";"):
            query = query.strip()[:-1]

        df = await self._query_client(query)
        results = df.to_dict(orient="records")

        return cast(list[dict[str, Any]], results)

    async def list_tables(self) -> List[str]:
        """List all tables available in pyoso server."""
        df = await self._query_client("SHOW TABLES")

        tables = df.to_dict(orient="records")

        table_names = [str(item["Table"]) for item in tables]
        return table_names

    async def get_table_schema(self, table_name: str) -> List[ColumnSchema]:
        """Get the schema of a specific table from the pyoso server."""
        df = await self._query_client(f"DESCRIBE {table_name}")
        results = df.to_dict(orient="records")
        typed_results = [
            ColumnSchema(
                name=item["Column"], type=item["Type"], description=item["Comment"]
            )
            for item in results
        ]
        return typed_results
