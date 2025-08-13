from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def parse_website_artifact(
    evaluator: MacroEvaluator,
    url_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses a generic website URL to extract artifact details.
    
    Args:
        evaluator: The MacroEvaluator instance.
        url_expr: SQLGlot expression representing the URL column.
    
    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=exp.Upper(this=exp.Literal.string('WWW')), alias=exp.Identifier(this="artifact_source")),
            exp.Alias(this=exp.Lower(this=exp.Literal.string('')), alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=exp.Lower(this=url_expr), alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=exp.Lower(this=url_expr), alias=exp.Identifier(this="artifact_url")),
            exp.Alias(this=exp.Upper(this=exp.Literal.string('WEBSITE')), alias=exp.Identifier(this="artifact_type")),
        ]
    )
    return exp.Subquery(this=select_expr)
