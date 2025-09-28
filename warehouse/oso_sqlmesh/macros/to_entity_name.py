from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def to_entity_name(
    evaluator: MacroEvaluator, string_expr: exp.ExpOrStr
) -> exp.Expression:
    """
    Lowercase a string expression and replace spaces with underscores.
    """
    arg = (
        string_expr
        if isinstance(string_expr, exp.Expression)
        else evaluator.parse_one(str(string_expr))
    )
    return exp.func(
        "REPLACE", exp.Lower(this=arg), exp.Literal.string(" "), exp.Literal.string("_")
    )
