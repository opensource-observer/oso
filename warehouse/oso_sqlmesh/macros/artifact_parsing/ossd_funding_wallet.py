from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def create_ossd_funding_wallet_artifact(
    evaluator: MacroEvaluator,
    project_name_expr: exp.Expression,
) -> exp.Expression:
    """
    Creates wallet artifact details for OSSD funding projects.

    Args:
        evaluator: The MacroEvaluator instance.
        project_name_expr: SQLGlot expression for the project name.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    artifact_url_expr = exp.Concat(
        expressions=[
            exp.Literal.string('https://www.opensource.observer/projects/'),
            project_name_expr
        ],
        safe=True # Assuming safe concatenation
    )

    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=exp.Upper(this=exp.Literal.string('OSS_DIRECTORY')), alias=exp.Identifier(this="artifact_source")),
            exp.Alias(this=exp.Lower(this=exp.Literal.string('oso')), alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=exp.Lower(this=project_name_expr), alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=exp.Lower(this=artifact_url_expr), alias=exp.Identifier(this="artifact_url")),
            exp.Alias(this=exp.Upper(this=exp.Literal.string('WALLET')), alias=exp.Identifier(this="artifact_type")),
        ]
    )
    return exp.Subquery(this=select_expr)
