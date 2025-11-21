from queryrewriter.types import TableResolver
from sqlglot import exp


class LegacyTableResolver(TableResolver):
    """Legacy table resolver for OSO tables based on legacy rules of the
    original data warehouse implementation. This is likely to be deprecated in
    the future, but is kept for backward compatibility."""

    def resolve_legacy_table(self, table: exp.Table) -> str | None:
        """Legacy fully qualified name resolver for OSO tables."""
        if not table.catalog and not table.db:
            return f"iceberg.oso.{table.name}"
        if table.db == "oso":
            return f"iceberg.{table.db}.{table.name}"
        return None

    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
    ) -> dict[str, exp.Table]:
        resolved: dict[str, exp.Table] = {}
        for table_name, table in tables.items():
            legacy_fqn = self.resolve_legacy_table(table)
            if legacy_fqn is not None:
                resolved[table_name] = exp.to_table(legacy_fqn)
            else:
                resolved[table_name] = table
        return resolved
