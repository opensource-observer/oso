import typing as t

from scheduler.graphql_client.base_model import UnsetType
from scheduler.graphql_client.resolve_tables import ResolveTables
from scheduler.testing.resources.codegen.oso_client import FakeClientProtocol


class FakeOSOClient(FakeClientProtocol):
    async def resolve_tables(
        self,
        references: list[str],
        metadata: t.Union[t.Optional[t.Any], UnsetType] = None,
        **kwargs,
    ) -> ResolveTables:
        from scheduler.graphql_client import (
            ResolveTablesSystem,
            ResolveTablesSystemResolveTables,
        )

        return ResolveTables(
            system=ResolveTablesSystem(
                resolveTables=[
                    ResolveTablesSystemResolveTables(
                        reference=table_name,
                        fqn=table_name,
                    )
                    for table_name in references
                ]
            )
        )
