from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def parse_github_repository_artifact(
    evaluator: MacroEvaluator,
    url_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses a GitHub repository URL to extract artifact details.
    Uses @url_parts to extract owner and repository name.

    Args:
        evaluator: The MacroEvaluator instance.
        url_expr: SQLGlot expression representing the GitHub URL column.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    # Extract owner (part 2) and repo name (part 3) from the URL
    # First remove protocol (https://)
    without_protocol = exp.SplitPart(
        this=url_expr,
        delimiter=exp.Literal.string("://"),
        part_index=exp.Literal.number(2)
    )
    
    # Extract owner (2nd part after splitting on /)
    owner_expr = exp.SplitPart(
        this=without_protocol,
        delimiter=exp.Literal.string("/"),
        part_index=exp.Literal.number(2)
    )
    
    # Extract repo name (3rd part after splitting on /)
    repo_expr = exp.SplitPart(
        this=without_protocol,
        delimiter=exp.Literal.string("/"),
        part_index=exp.Literal.number(3)
    )
    
    # Construct the artifact URL
    artifact_url_expr = exp.Lower(
        this=exp.Concat(
            expressions=[
                exp.Literal.string('https://github.com/'),
                owner_expr,
                exp.Literal.string('/'),
                repo_expr
            ],
            safe=True
        )
    )
    
    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=exp.Upper(this=exp.Literal.string('GITHUB')), alias=exp.Identifier(this="artifact_source")),
            exp.Alias(this=exp.Lower(this=owner_expr), alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=exp.Lower(this=repo_expr), alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=artifact_url_expr, alias=exp.Identifier(this="artifact_url")),
            exp.Alias(this=exp.Upper(this=exp.Literal.string('REPOSITORY')), alias=exp.Identifier(this="artifact_type")),
        ]
    )
    return exp.Subquery(this=select_expr)
   