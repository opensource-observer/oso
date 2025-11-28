import logging
import typing as t

from queryrewriter.dialect import extend_sqlglot, parse
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import Scope, build_scope

from .types import TableResolver

logger = logging.getLogger(__name__)

_extended_sqlglot = False

TableFQNResolver = t.Callable[[exp.Table], str | None]


def safe_extend_sqlglot():
    """This will only extend sqlglot once in any given process."""
    from sqlglot import parse_one
    from sqlglot.errors import ParseError

    global _extended_sqlglot

    if _extended_sqlglot:
        return

    try:
        import sqlmesh  # noqa: F401

        logger.debug("sqlmesh is installed, assuming sqlglot is already extended.")
    except ImportError:
        try:
            mf = parse_one("@fake_macro('what')")
            if mf.__class__.__name__ != "MacroFunc":
                logger.debug("sqlmesh is not installed, extending sqlglot.")
                extend_sqlglot()
        except ParseError:
            logger.debug("sqlmesh is not installed, extending sqlglot.")
            extend_sqlglot()


def default_table_to_fqn(
    org_name: str, default_dataset_name: str | None
) -> TableFQNResolver:
    """
    Converts a sqlglot Table expression to a fully qualified table name.

    Args:
        org_name (str): The organization name.
        dataset_name (str): The dataset name.
        table (exp.Table): The sqlglot Table expression.

    Returns:
        str: The fully qualified table name.
    """

    def _resolver(table: exp.Table) -> str | None:
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

    return _resolver


TransformCallable = t.Callable[[exp.Expression], exp.Expression | None]


def table_transformer(table: exp.Table, new_table: exp.Table) -> TransformCallable:
    def _transform(node: exp.Expression):
        if node == table:
            return new_table
        return node

    return _transform


def find_all_table_sources(expr: exp.Expression) -> set[exp.Table]:
    """Find all table sources in a sqlglot expression."""

    def _recurse_table_scope_for_tables(scope_name: str | None, scope: Scope):
        tables: set[exp.Table] = set()
        for inner_scope_name, source in scope.sources.items():
            if isinstance(source, exp.Table):
                if not source.db and source.name == scope_name:
                    error_message = f"{source.name} is a either a circular reference. This is due to overloading the name `{source.name}`. Please use the form <dataset>.<table> to refer to tables where possible."
                    raise ValueError(error_message)
                tables.add(source)
            elif isinstance(source, Scope):
                new_tables = _recurse_table_scope_for_tables(inner_scope_name, source)
                tables = tables.union(new_tables)
            else:
                raise ValueError(f"Unhandled source type: {type(source)}")
        for union_scope in scope.union_scopes:
            new_tables = _recurse_table_scope_for_tables(scope_name, union_scope)
            tables = tables.union(new_tables)
        return tables

    scope = build_scope(expr)
    if not scope:
        raise ValueError("Could not build scope for expression.")
    return _recurse_table_scope_for_tables(None, scope)


def apply_transforms_to_expression(
    expr: exp.Expression, transforms: list[TransformCallable]
) -> exp.Expression:
    for transform in transforms:
        expr = expr.transform(transform, copy=True)
    return expr


def raw_table_to_reference(
    table: exp.Table,
) -> str:
    assert table.name, "Table must have a name."
    if table.catalog and table.db:
        return f"{table.catalog}.{table.db}.{table.name}"
    if table.db:
        return f"{table.db}.{table.name}"
    return table.name


async def rewrite_query(
    query: str,
    table_resolvers: list[TableResolver],
    *,
    metadata: dict | None = None,
    dialect: str = "trino",
) -> str:
    """
    Rewrites a SQL query written in the sqlmesh dialect using the provided table
    resolver.

    Args:
        org_name (str): The organization name for the query. This is either the
            user making the query or the org the query is being made on behalf of.
        query (str): The original SQL query.
        table_resolvers (list[TableResolver]): A list of instances that resolve
            table names. The resolvers will be applied in order.
        default_dataset_name (str | None): The default dataset name to use when
            a table does not have a dataset specified.
        dialect (str): The SQL dialect to use for the final rendering of the query.

    Returns:
        str: The rewritten SQL query.
    """

    safe_extend_sqlglot()

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

    # By default, assume all tables are resolved as-is
    resolved_tables_dict = {
        raw_table_to_reference(table): table for table in table_references
    }

    # Each resolver gets to transform the set of resolved tables in order. This
    # allows earlier resolvers to act as middleware.
    for resolver in table_resolvers:
        resolved_tables_dict = await resolver.resolve_tables(resolved_tables_dict)

    # Rewrite the query with resolved table names
    rewritten_statements: list[exp.Expression] = []

    table_rewriters: list[TransformCallable] = []

    for table in table_references:
        fqn = raw_table_to_reference(table)

        # Get the resolved table info
        resolved_table = resolved_tables_dict.get(fqn)

        if not resolved_table:
            raise ValueError(f"Table {fqn} could not be resolved.")

        qualified_resolved_table = qualify(resolved_table)
        assert isinstance(qualified_resolved_table, exp.Table), (
            "Resolved table is not a Table expression."
        )

        # Ensure alias is preserved
        if table.alias:
            qualified_resolved_table.set("alias", table.alias)

        # Create a transformation function for this table expression
        table_rewriters.append(table_transformer(table, qualified_resolved_table))

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
