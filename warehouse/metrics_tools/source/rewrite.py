"""Source rewriting tools for the oso sqlmesh configuration"""

import typing as t

from sqlglot import exp
from sqlmesh import ExecutionContext

DUCKDB_REWRITE_RULES: t.List[dict] = [
    {
        "catalog": "*",
        "db": "*",
        "table": "*",
        "replace": "sources__{catalog}__{db}.{table}",
    }
]

LOCAL_TRINO_REWRITE_RULES: t.List[dict] = [
    {
        "catalog": "*",
        "db": "*",
        "table": "*",
        "replace": "{catalog}.bq_{db}.{table}",
    }
]


def oso_source_for_pymodel(context: ExecutionContext, table_name: str) -> exp.Table:
    # Rewrite rules can be injected into the sqlmesh context via the sqlmesh
    # config. However, in general we don't want to modify the source unless it's
    # running on duckdb locally. So this allows rewriting as an override but
    # defaults to using duckdb if we're currently running duckdb.
    oso_source_rewrite_config_default: t.List[dict] = []
    if context.engine_adapter.dialect == "duckdb":
        oso_source_rewrite_config_default = DUCKDB_REWRITE_RULES
    if context.gateway == "local-trino":
        oso_source_rewrite_config_default = LOCAL_TRINO_REWRITE_RULES
    oso_source_rewrite_config = t.cast(
        t.List[dict],
        context.var("oso_source_rewrite", oso_source_rewrite_config_default),
    )
    return oso_source_rewrite(oso_source_rewrite_config, table_name)


def oso_source_rewrite(
    oso_source_rewrite_config: t.List[dict], table: exp.Table | str
) -> exp.Table:
    # try to find a matching rule if none then we return the table
    if isinstance(table, str):
        table = exp.to_table(table)
    rewritten_table = table
    for rewrite in oso_source_rewrite_config:
        catalog_match = rewrite.get("catalog")
        assert catalog_match is not None, "catalog is required in rewrite"
        db_match = rewrite.get("db")
        assert db_match is not None, "db is required in rewrite"
        table_match = rewrite.get("table")
        assert table_match is not None, "table is required in rewrite"
        replace = rewrite.get("replace")
        assert replace is not None, "replace is required in rewrite"
        catalog_match = t.cast(str, catalog_match)
        db_match = t.cast(str, db_match)
        table_match = t.cast(str, table_match)
        replace = t.cast(str, replace)
        if (
            (catalog_match == "*" or catalog_match == table.catalog)
            and (db_match == "*" or db_match == table.db)
            and (table_match == "*" or table_match == table.this.this)
        ):
            rewritten_table = exp.to_table(
                replace.format(
                    catalog=table.catalog, db=table.db, table=table.this.this
                )
            )
            break
    return rewritten_table
