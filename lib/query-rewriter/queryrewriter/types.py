import typing as t


class TableResolverProtocol(t.Protocol):
    async def resolve_tables(self, tables: t.List[str]) -> t.Dict[str, str]: ...
