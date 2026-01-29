import logging
import typing as t

from queryrewriter.dialect import extend_sqlglot, parse
from queryrewriter.errors import TableResolutionError
from sqlglot import exp
from sqlglot.optimizer.qualify_tables import qualify_tables
from sqlglot.optimizer.scope import Scope, build_scope

from .types import RewriteResponse, TableResolver

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

    def _recurse_table_scope_for_tables(
        scope_name: str | None,
        scope: Scope,
        visited: set[Scope],
        recursion_stack: list[Scope],
    ):
        tables: set[exp.Table] = set()
        for inner_scope_name, source in scope.sources.items():
            if isinstance(source, exp.Table):
                if not source.db and source.name == scope_name:
                    error_message = f"{source.name} is a either a circular reference. This is due to overloading the name `{source.name}`. Please use the form <dataset>.<table> to refer to tables where possible."
                    raise ValueError(error_message)
                tables.add(source)
            elif isinstance(source, Scope):
                if source in recursion_stack:
                    raise ValueError(
                        f"Circular reference detected in query with name {scope_name}. From {recursion_stack}"
                    )
                if source in visited:
                    continue
                visited.add(source)
                new_stack = recursion_stack + [source]
                new_tables = _recurse_table_scope_for_tables(
                    inner_scope_name, source, visited, new_stack
                )
                tables = tables.union(new_tables)
            else:
                raise ValueError(f"Unhandled source type: {type(source)}")
        for union_scope in scope.union_scopes:
            new_tables = _recurse_table_scope_for_tables(
                scope_name, union_scope, visited, recursion_stack
            )
            tables = tables.union(new_tables)
        return tables

    scope = build_scope(expr)
    if not scope:
        # If there is no scope, we might not have any tables, for example: SHOW CATALOGS.
        return set()
    return _recurse_table_scope_for_tables(
        None, scope, visited=set(), recursion_stack=[]
    )


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
    input_dialect: str = "trino",
    output_dialect: str | None = None,
    prepend_resolved_tables_comment: bool = True,
) -> RewriteResponse:
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
        input_dialect (str): The input SQL dialect to use for the query.
        output_dialect (str | None): The output SQL dialect to use for the final
            rendering of the query. If None, uses the input dialect.
        prepend_resolved_tables_comment (bool): Whether to prepend a comment with
            resolved table information to the rewritten query.

    Returns:
        str: The rewritten SQL query.
    """
    output_dialect = output_dialect or input_dialect

    safe_extend_sqlglot()

    # Parse the query. It could be many statements
    statements = parse(query, default_dialect=input_dialect)

    # Qualify all the statements. This is just good form to ensure consistent
    # rewriting comparisons for tests
    qualified_statements = [qualify_tables(statement) for statement in statements]

    logger.debug("Finding table references in query statements.")
    # For each statement, find table references and store the references. We
    # will resolve all the table names at once and rewrite the query at the end.
    table_references: set[exp.Table] = set()
    for statement in qualified_statements:
        tables_in_statement = find_all_table_sources(statement)
        table_references = table_references.union(tables_in_statement)

    logger.debug(f"Found {len(table_references)} table references in query.")

    # By default, assume all tables are resolved as-is
    resolved_tables_dict = {
        raw_table_to_reference(table): table for table in table_references
    }

    # Each resolver gets to transform the set of resolved tables in order. This
    # allows earlier resolvers to act as middleware.
    for resolver in table_resolvers:
        resolved_tables_dict = await resolver.resolve_tables(resolved_tables_dict)

    # Rewrite the query with resolved table names
    logger.debug("Rewriting query with resolved table names.")
    rewritten_statements: list[exp.Expression] = []

    table_rewriters: list[TransformCallable] = []

    unresolved_tables: list[exp.Table] = []

    for table in table_references:
        fqn = raw_table_to_reference(table)

        # Get the resolved table info
        resolved_table = resolved_tables_dict.get(fqn)

        if not resolved_table:
            unresolved_tables.append(table)
            continue

        resolved_table = resolved_table.copy()

        qualified_resolved_table = qualify_tables(resolved_table)
        assert isinstance(qualified_resolved_table, exp.Table), (
            "Resolved table is not a Table expression."
        )

        # Ensure alias is preserved
        if table.alias:
            qualified_resolved_table.set("alias", table.alias)

        # Create a transformation function for this table expression
        table_rewriters.append(table_transformer(table, qualified_resolved_table))

    if unresolved_tables:
        raise TableResolutionError(
            [raw_table_to_reference(table) for table in unresolved_tables]
        )

    for statement in qualified_statements:
        rewritten = apply_transforms_to_expression(statement, table_rewriters)
        rewritten_statements.append(rewritten)

    if prepend_resolved_tables_comment:
        # Prepends a comment with all the resolved tables for easy debugging on
        # the warehouse.
        resolved_tables_comments: list[str] = ["Table Rewrite Map:"]
        for orig_table_str, warehouse_table in resolved_tables_dict.items():
            resolved_tables_comments.append(
                f"  {orig_table_str} -> {raw_table_to_reference(warehouse_table)}"
            )

        first_statement = rewritten_statements[0]
        first_statement.add_comments(resolved_tables_comments, prepend=True)

    # Convert rewritten statements back to SQL
    rewritten_sql_statements = [
        rewritten_statement.sql(dialect=output_dialect)
        for rewritten_statement in rewritten_statements
    ]
    rewritten_sql = ";\n".join(rewritten_sql_statements)

    return RewriteResponse(
        rewritten_query=rewritten_sql,
        tables={
            raw_table_to_reference(orig_table): raw_table_to_reference(
                resolved_tables_dict[raw_table_to_reference(orig_table)]
            )
            for orig_table in table_references
        },
    )
