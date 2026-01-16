import typing as t
from unittest.mock import AsyncMock, create_autospec

import pytest
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.graphql_client.resolve_tables import (
    ResolveTables,
    ResolveTablesSystem,
    ResolveTablesSystemResolveTables,
)
from scheduler.utils import OSOClientTableResolver
from sqlglot import exp


def fake_oso_client(respond_with_tables: list[str]):
    client = create_autospec(OSOClient, instance=True)
    resolve_tables: list[ResolveTablesSystemResolveTables] = [
        ResolveTablesSystemResolveTables(
            reference=table_name,
            fqn=f"fake.fqn.{table_name}",
        )
        for i, table_name in enumerate(respond_with_tables)
    ]
    client.resolve_tables.return_value = ResolveTables(
        system=ResolveTablesSystem(resolveTables=resolve_tables)
    )
    return client


@pytest.mark.asyncio
async def test_resolve_tables_correctly():
    oso_client = fake_oso_client(respond_with_tables=["table1"])
    resolver = OSOClientTableResolver(t.cast(OSOClient, oso_client))
    await resolver.resolve_tables(
        {
            "table1": exp.to_table("table1"),
        }
    )


@pytest.mark.asyncio
async def test_resolve_tables_should_fail_no_tables():
    oso_client = fake_oso_client(respond_with_tables=["table1"])
    resolver = OSOClientTableResolver(t.cast(OSOClient, oso_client))

    result = await resolver.resolve_tables(
        {
            "table1": exp.to_table("table1"),
            "table2": exp.to_table("table2"),
        }
    )
    assert isinstance(oso_client.resolve_tables, AsyncMock)
    oso_client.resolve_tables.assert_called()

    assert result["table1"] == exp.to_table("fake.fqn.table1")
    assert result.get("table2") is None
