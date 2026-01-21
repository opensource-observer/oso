import typing as t
from unittest.mock import Mock, create_autospec

from scheduler.graphql_client.client import Client as OSOClient
from scheduler.graphql_client.resolve_tables import (
    ResolveTables,
    ResolveTablesSystem,
    ResolveTablesSystemResolveTables,
)
from scheduler.types import Model, UserDefinedModelStateClient


class FakeUDMClient(UserDefinedModelStateClient):
    def __init__(self):
        self._models: list[Model] = []
        super().__init__()

    async def all_models_missing_runs(self) -> list[Model]:
        return self._models

    def add_model(self, model: Model) -> None:
        self._models.append(model)


class MockOSOClientController:
    def __init__(self, oso_client: t.Any = None):
        self._client = oso_client or create_autospec(OSOClient, instance=True)

    @property
    def as_mock(self) -> Mock:
        return self._client

    def set_resolve_tables_response(self, tables: list[str]) -> None:
        resolve_tables: list[ResolveTablesSystemResolveTables] = [
            ResolveTablesSystemResolveTables(
                reference=table_name,
                fqn=f"fake.fqn.{table_name}",
            )
            for i, table_name in enumerate(tables)
        ]
        self._client.resolve_tables.return_value = ResolveTables(
            system=ResolveTablesSystem(resolveTables=resolve_tables)
        )

    @property
    def as_oso_client(self) -> OSOClient:
        return t.cast(OSOClient, self._client)


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
