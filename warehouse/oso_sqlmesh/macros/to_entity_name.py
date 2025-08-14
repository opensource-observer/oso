from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def to_entity_name(
    evaluator: MacroEvaluator, string_expr: exp.ExpOrStr
) -> exp.Expression:
    """
    Takes a string expression, lowercases it and replaces spaces with underscores.
    Useful for creating consistent entity names from display names.
    """

    # First lowercase the string
    lowercased = exp.Lower(this=string_expr)

    # Then replace spaces with underscores using REPLACE function
    entity_name = exp.Anonymous(
        this="REPLACE",
        expressions=[lowercased, exp.Literal.string(" "), exp.Literal.string("_")],
    )

    return entity_name
