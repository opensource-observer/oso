from typing import Any, Generator

import pyarrow as pa
from cloudquery.sdk.scheduler import TableResolver
from cloudquery.sdk.schema import Column
from cloudquery.sdk.schema import Table
from cloudquery.sdk.types import JSONType

from ..client import Client


class ExampleTable(Table):
    def __init__(self) -> None:
        super().__init__(
            name="example_table",
            title="An Example Table",
            columns=[
                Column("id", pa.string(), primary_key=True),
                Column("created_at", pa.timestamp(unit="s")),
                Column("last_updated_at", pa.timestamp(unit="s")),
                Column("name", pa.string()),
                Column("data", JSONType()),
            ],
            relations=[],
        )

    @property
    def resolver(self):
        return ExampleResolver(table=self)


class ExampleResolver(TableResolver):
    def __init__(self, table=None) -> None:
        super().__init__(table=table)

    def resolve(self, client: Client, parent_resource) -> Generator[Any, None, None]:
        for row in client.client.load_rows():
            yield row

    @property
    def child_resolvers(self):
        return [table.resolver for table in self._table.relations]
