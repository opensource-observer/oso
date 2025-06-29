from sqlglot import exp


def hash_expressions(
    *expressions: exp.Expression, dialect: str = "duckdb"
) -> exp.Expression:
    """Given the expressions return a sql expression that hashes them together.

    This is useful for creating a deterministic ID from multiple columns or values.
    """
    # Convert all expressions to strings
    expressions_cast_to_str = [
        exp.Cast(this=expr, to=exp.DataType.build("VARCHAR")) for expr in expressions
    ]
    concatenated = exp.Concat(
        expressions=expressions_cast_to_str, safe=True, coalesce=False
    )
    if dialect == "trino":
        # Trino's SHA256 function only accepts type `varbinary`. So we convert
        # the varchar to varbinary with trino's to_utf8.
        concatenated = exp.Anonymous(this="to_utf8", expressions=[concatenated])
    sha = exp.SHA2(
        this=concatenated,
        length=exp.Literal(this=256, is_string=False),
    )
    return sha


def exp_to_str(expression: exp.Expression | str) -> str:
    if isinstance(expression, str):
        return expression
    if isinstance(expression, exp.Literal):
        return str(expression.this)
    elif isinstance(expression, exp.Identifier):
        return str(expression.this)
    else:
        return str(expression)
