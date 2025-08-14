from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def parse_defillama_artifact(
    evaluator: MacroEvaluator,
    url_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses a DefiLlama URL to extract artifact details.

    Args:
        evaluator: The MacroEvaluator instance.
        url_expr: SQLGlot expression representing the DefiLlama URL column.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    artifact_name_expr = exp.Case().when(
        exp.Like(this=url_expr, expression=exp.Literal.string('https://defillama.com/protocol/%')),
        exp.Substring(this=url_expr, start=exp.Literal.number(32))
    ).else_(
        url_expr # Default
    )

    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=exp.Upper(this=exp.Literal.string('DEFILLAMA')), alias=exp.Identifier(this="artifact_source")),
            exp.Alias(this=exp.Lower(this=exp.Literal.string('')), alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=exp.Lower(this=artifact_name_expr), alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=exp.Lower(this=url_expr), alias=exp.Identifier(this="artifact_url")),
            exp.Alias(this=exp.Upper(this=exp.Literal.string('DEFILLAMA_PROTOCOL')), alias=exp.Identifier(this="artifact_type")),
        ]
    )
    return exp.Subquery(this=select_expr)
