from queryrewriter.types import TableResolver
from sqlglot import exp


class InferFQN(TableResolver):
    def __init__(
        self,
        org_name: str,
        default_dataset_name: str | None,
    ):
        self.org_name = org_name
        self.default_dataset_name = default_dataset_name

    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
    ) -> dict[str, exp.Table]:
        resolved: dict[str, exp.Table] = {}
        for table_name, table in tables.items():
            fqn = self.infer_table_fqn(table)
            resolved[table_name] = exp.to_table(fqn)
        return resolved

    def infer_table_fqn(
        self,
        table: exp.Table,
    ) -> str:
        catalog = table.catalog or self.org_name
        db = table.db or self.default_dataset_name
        if not db:
            raise ValueError(
                f"Table {table} is missing a dataset name and is not provided."
            )
        name = table.name
        return f"{catalog}.{db}.{name}"
