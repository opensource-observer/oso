import typing as t

from sqlglot import exp
from sqlmesh.core.dialect import parse, parse_one


def hash_expressions(*expressions: exp.Expression, dialect: str = "duckdb") -> exp.Expression:
    """Given the expressions return a sql expression that hashes them together.
    
    This is useful for creating a deterministic ID from multiple columns or values.
    """
    # Convert all expressions to strings
    expressions_cast_to_str = [
        exp.Cast(this=expr, to=exp.DataType.build("VARCHAR"))
        for expr in expressions
    ]
    concatenated = exp.Concat(expressions=expressions_cast_to_str, safe=True, coalesce=False)
    if dialect == "trino":
        # Trino's SHA256 function only accepts type `varbinary`. So we convert
        # the varchar to varbinary with trino's to_utf8.
        concatenated = exp.Anonymous(this="to_utf8", expressions=[concatenated])
    sha = exp.SHA2(
        this=concatenated,
        length=exp.Literal(this=256, is_string=False),
    )
    return sha


def coerce_to_column(column: str | exp.Expression) -> exp.Expression:
    if isinstance(column, str):
        return exp.to_column(column)
    elif isinstance(column, exp.Expression):
        return column
    raise ValueError(f"Invalid column type: {column}")


def coerce_to_table(table: str | exp.Expression) -> exp.Expression:
    if isinstance(table, str):
        return exp.to_table(table)
    elif isinstance(table, exp.Expression):
        return table
    raise ValueError(f"Invalid table type: {table}")


def coerce_to_expression(
    val: exp.ExpOrStr, coerce_type: exp.IntoType, dialect: t.Optional[str] = None
) -> exp.Expression:
    if isinstance(val, exp.Expression):
        return val
    elif isinstance(val, str):
        return parse_one(val, dialect=dialect, into=coerce_type)
    raise ValueError(f"Invalid value type: {val}")


def literal_or_expression(val: exp.ExpOrStr | int | float) -> exp.Expression:
    if isinstance(val, exp.Expression):
        return val
    elif isinstance(val, str):
        return exp.Literal(this=val, is_string=True)
    else:
        return exp.Literal(this=val, is_string=False)


def exp_literal_to_py_literal(glot_literal: exp.Expression) -> t.Any:
    # Don't error by default let it pass
    if not isinstance(glot_literal, exp.Literal):
        return glot_literal
    return glot_literal.this


def exp_to_int(glot_expression: exp.Expression) -> int:
    if isinstance(glot_expression, exp.Literal):
        return int(glot_expression.this)
    elif isinstance(glot_expression, exp.Neg):
        return int(glot_expression.this.this) * -1
    raise ValueError(f"Invalid expression type: {glot_expression}")


def str_or_expressions(query: str | t.List[exp.Expression]) -> t.List[exp.Expression]:
    if not isinstance(query, list):
        return parse(query)
    return query

def exp_to_str(expression: exp.Expression | str) -> str:
    if isinstance(expression, str):
        return expression
    if isinstance(expression, exp.Literal):
        return str(expression.this)
    elif isinstance(expression, exp.Identifier):
        return str(expression.this)
    else:
        return str(expression)