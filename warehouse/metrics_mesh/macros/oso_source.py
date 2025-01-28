import typing as t

from metrics_tools.source.rewrite import DUCKDB_REWRITE_RULES, oso_source_rewrite
from sqlglot import exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


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

    if evaluator.runtime_stage == "loading":
        return table

    if evaluator.engine_adapter.dialect == "duckdb":
        # We hardcode the rewrite rules for duckdb here to 1) keep things consistent
        # and 2) ensure tests can run even on production when using duckdb
        oso_source_rewrite_config = DUCKDB_REWRITE_RULES
    else:
        oso_source_rewrite_config = t.cast(
            t.List[dict], evaluator.var("oso_source_rewrite", [])
        )

    return oso_source_rewrite(oso_source_rewrite_config, table)
