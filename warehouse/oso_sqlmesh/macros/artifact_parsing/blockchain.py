from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def parse_blockchain_artifact(
    evaluator: MacroEvaluator,
    address_expr: exp.Expression
) -> exp.Expression:
    """
    Parses blockchain artifact details from OSSD.

    Args:
        evaluator: The MacroEvaluator instance.
        address_expr: SQLGlot expression for the blockchain address.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url
    """
    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=exp.Lower(this=exp.Literal.string('')), alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=exp.Lower(this=address_expr), alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=exp.Lower(this=address_expr), alias=exp.Identifier(this="artifact_url")),
        ]
    )
    return exp.Subquery(this=select_expr)
