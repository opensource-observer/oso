import typing as t

from sqlglot import exp
from sqlmesh import ExecutionContext, macro
from sqlmesh.core.macros import MacroEvaluator


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


def oso_source_for_pymodel(context: ExecutionContext, table_name: str) -> exp.Table:
    oso_source_rewrite_config = t.cast(
        t.List[dict], context.var("oso_source_rewrite", [])
    )
    return oso_source_rewrite(oso_source_rewrite_config, table_name)


@macro()
def oso_source(evaluator: MacroEvaluator, table_name: exp.Expression):
    """Translates a table reference to a table reference valid in the current
    sqlmesh gateway. The table refernce should be the string to the table on
    production trino.

    Configuration for the table rewriting is done through the variable
    `oso_source_rewrite` in the sqlmesh configuration. This variable should be set
    for every gateway. This variable should be a list of dictionaries. The
    dictionaries should have the following fields:

    - `catalog`: The catalog of the table to match. Use `*` to match all.
    - `db`: The database of the table to match. Use `*` to match all databases.
    - `table`: The table to match. Use `*` to match all tables.
    - `replace`: The replacement table reference. These can be format strings
      with `{catalog}`, `{db}`, and `{table}` variables from the parsed table
      reference.

    Example:

    Given this configuration:

        ```python
        oso_source_rewrite = [
            { "catalog": "bigquery", "db": "*", "table": "*", replace:
            "source_{db}.{table}" }
        ]
        ```
    Using `@oso_source` in a query like:

        ```sql
        select * from @oso_source("bigquery.public.table")
        ```

    Will be rewritten to:

        ```sql
        select * from source_public.table
        ```
    """
    table_name_evaled = evaluator.eval_expression(table_name)

    if isinstance(table_name_evaled, str):
        table = exp.to_table(table_name_evaled)
    elif isinstance(table_name_evaled, (exp.Literal, exp.Identifier)):
        table = exp.to_table(table_name_evaled.this)
    elif isinstance(table_name_evaled, exp.Table):
        table = table_name_evaled
    else:
        raise ValueError(f"Unexpected table name: {table_name_evaled}")

    oso_source_rewrite_config = t.cast(
        t.List[dict], evaluator.var("oso_source_rewrite", [])
    )

    return oso_source_rewrite(oso_source_rewrite_config, table)
