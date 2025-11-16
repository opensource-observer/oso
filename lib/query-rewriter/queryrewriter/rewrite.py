import typing as t

from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import Scope, build_scope
from sqlmesh.core.dialect import parse

from .types import TableResolverProtocol


def table_to_fqn(
    org_name: str, table: exp.Table, default_dataset_name: str | None
) -> str:
    """
    Converts a sqlglot Table expression to a fully qualified table name.

    Args:
        org_name (str): The organization name.
        dataset_name (str): The dataset name.
        table (exp.Table): The sqlglot Table expression.

    Returns:
        str: The fully qualified table name.
    """
    catalog = table.catalog or org_name
    db = table.db
    if not db:
        if default_dataset_name is None:
            raise ValueError(
                f"Table {table} is missing a dataset name and is not provided."
            )
        db = default_dataset_name
    name = table.name
    return f"{catalog}.{db}.{name}"


TransformCallable = t.Callable[[exp.Expression], exp.Expression | None]


def table_transformer(table: exp.Table, new_table: exp.Table) -> TransformCallable:
    def _transform(node: exp.Expression):
        if node == table:
            return new_table
        return node

    return _transform


def find_all_table_sources(expr: exp.Expression) -> set[exp.Table]:
    """Find all table sources in a sqlglot expression."""

    def _recurse_table_scope_for_tables(scope: Scope):
        tables: set[exp.Table] = set()
        for source in scope.sources.values():
            if isinstance(source, exp.Table):
                tables.add(source)
            elif isinstance(source, Scope):
                tables = _recurse_table_scope_for_tables(source)
                tables = tables.union(tables)
            else:
                raise ValueError(f"Unhandled source type: {type(source)}")
        return tables

    scope = build_scope(expr)
    if not scope:
        raise ValueError("Could not build scope for expression.")
    return _recurse_table_scope_for_tables(scope)


def apply_transforms_to_expression(
    expr: exp.Expression, transforms: list[TransformCallable]
) -> exp.Expression:
    for transform in transforms:
        expr = expr.transform(transform, copy=True)
    return expr


async def rewrite_query(
    org_name: str,
    query: str,
    table_resolver: TableResolverProtocol,
    *,
    default_dataset_name: str | None = None,
    dialect: str = "trino",
) -> str:
    """
    Rewrites a SQL query written in the sqlmesh dialect using the provided table
    resolver.

    Args:
        org_name (str): The organization name for the query. This is either the
            user making the query or the org the query is being made on behalf of.
        query (str): The original SQL query. table_resolver
        (TableResolverProtocol): An instance that resolves table names.
    Returns:
        str: The rewritten SQL query.
    """

    # Parse the query. It could be many statements
    statements = parse(query)

    # Qualify all the statements. This is just good form to ensure consistent
    # rewriting comparisons for tests
    qualified_statements = [qualify(statement) for statement in statements]

    # For each statement, find table references and store the references. We
    # will resolve all the table names at once and rewrite the query at the end.
    table_references: set[exp.Table] = set()
    for statement in qualified_statements:
        tables_in_statement = find_all_table_sources(statement)
        table_references = table_references.union(tables_in_statement)

    table_reference_names = [
        table_to_fqn(org_name, table, default_dataset_name=default_dataset_name)
        for table in table_references
    ]

    # Resolve table names using the provided resolver
    resolved_tables_dict = await table_resolver.resolve_tables(table_reference_names)

    # Rewrite the query with resolved table names
    rewritten_statements: list[exp.Expression] = []

    table_rewriters: list[TransformCallable] = []

    for table in table_references:
        fqn = table_to_fqn(org_name, table, default_dataset_name=default_dataset_name)

        # Get the resolved table info
        resolved_table_name = resolved_tables_dict.get(fqn)

        if not resolved_table_name:
            raise ValueError(f"Table {fqn} could not be resolved.")

        rewritten_table = t.cast(exp.Table, qualify(exp.to_table(resolved_table_name)))
        # Ensure alias is preserved
        if table.alias:
            rewritten_table.set("alias", table.alias)

        # Create a transformation function for this table expression
        table_rewriters.append(table_transformer(table, rewritten_table))

    for statement in qualified_statements:
        rewritten = apply_transforms_to_expression(statement, table_rewriters)
        rewritten_statements.append(rewritten)

    # Convert rewritten statements back to SQL
    rewritten_sql_statements = [
        rewritten_statement.sql(dialect=dialect)
        for rewritten_statement in rewritten_statements
    ]
    rewritten_sql = ";\n".join(rewritten_sql_statements)

    return rewritten_sql
