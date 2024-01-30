from typing import Any, Generator

import pyarrow as pa
from cloudquery.sdk.scheduler import TableResolver
from cloudquery.sdk.schema import Column
from cloudquery.sdk.schema import Table
from cloudquery.sdk.types import JSONType

from ..client import Client


class ContractUsageTable(Table):
    def __init__(self) -> None:
        super().__init__(
            name="contract_usage",
            title="Daily contract usage",
            columns=[
                Column("date", pa.date64()),
                Column("address", pa.string()),
                Column("user_address", pa.string()),
                Column("safe_address", pa.string()),
                Column("l2_gas", pa.string()),
                Column("l1_gas", pa.string()),
                Column("tx_count", pa.int64()),
            ],
            relations=[],
        )

    @property
    def resolver(self):
        return ContractUsageResolver(table=self)


class ContractUsageResolver(TableResolver):
    def __init__(self, table=None) -> None:
        super().__init__(table=table)

    def resolve(self, client: Client, parent_resource) -> Generator[Any, None, None]:
        for row in client.client.load_rows():
            yield {
                "date": row.date.datetime,
                "address": row.address,
                "user_address": row.user_address,
                "safe_address": row.safe_address,
                "l2_gas": str(row.l2_gas),
                "l1_gas": str(row.l1_gas),
                "tx_count": row.tx_count,
            }

    @property
    def child_resolvers(self):
        return []
